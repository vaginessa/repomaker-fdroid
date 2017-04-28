import datetime
import logging
import os
from io import BytesIO

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from fdroidserver import metadata
from hvad.models import TranslatableModel, TranslatedFields

from maker.storage import get_repo_file_path_for_app
from .category import Category
from .repository import Repository, RemoteRepository


class AbstractApp(TranslatableModel):
    package_id = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(max_length=2048, blank=True)
    icon = models.ImageField(upload_to=get_repo_file_path_for_app,
                             default=settings.APP_DEFAULT_ICON)
    category = models.ManyToManyField(Category, blank=True, limit_choices_to={'user': None})
    added_date = models.DateTimeField(default=timezone.now)
    translations = TranslatedFields(
        l_summary=models.CharField(max_length=255, blank=True, verbose_name=_("Summary")),
        l_description=models.TextField(blank=True, verbose_name=_("Description")),
    )

    def __str__(self):
        return self.name

    def delete_old_icon(self):
        icon_path = os.path.dirname(self.icon.path)
        if icon_path != settings.MEDIA_ROOT:
            self.icon.delete(save=False)

    class Meta:
        abstract = True
        unique_together = (("package_id", "repo"),)


class App(AbstractApp):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    last_updated_date = models.DateTimeField(auto_now=True)
    translations = TranslatedFields()  # required for i18n

    def get_absolute_url(self):
        return reverse('app', kwargs={'repo_id': self.repo.pk, 'app_id': self.pk})

    @staticmethod
    def from_remote_app(repo, app):
        """
        Returns an App in :param repo from the given RemoteApp :param app.

        Note that it does exclude the category. You need to add these after saving the app.
        """
        # TODO check how the icon extracted to repo/icons-640 could be used instead
        icon = ContentFile(app.icon.read())
        icon.name = os.path.basename(app.icon.name)
        return App(repo=repo, package_id=app.package_id, name=app.name, summary=app.summary,
                   description=app.description, website=app.website, icon=icon)

    def to_metadata_app(self):
        meta = metadata.App()
        meta.id = self.package_id
        meta.WebSite = self.website
        meta.Summary = self.summary
        meta.Description = self.description
        meta.added = timezone.make_naive(self.added_date)
        meta.Categories = [category.name for category in self.category.all()]
        meta['localized'] = self._get_screenshot_dict()
        return meta

    def _get_screenshot_dict(self):
        from . import Screenshot
        localized = dict()
        screenshots = Screenshot.objects.filter(app=self).all()
        for s in screenshots:
            if s.language_code not in localized:
                localized[s.language_code] = dict()
            if s.type not in localized[s.language_code]:
                localized[s.language_code][s.type] = []
            localized[s.language_code][s.type].append(os.path.basename(s.file.name))
        return localized


class RemoteApp(AbstractApp):
    repo = models.ForeignKey(RemoteRepository, on_delete=models.CASCADE)
    icon_etag = models.CharField(max_length=128, blank=True)
    last_updated_date = models.DateTimeField(blank=True)
    translations = TranslatedFields()  # required for i18n

    def update_from_json(self, app):
        """
        Updates the data for this app.
        :param app: A JSON app object from the repository v1 index.
        :return: True if app changed, False otherwise
        """

        # don't update if app hasn't changed since last update
        last_update = datetime.datetime.fromtimestamp(app['lastUpdated'] / 1000, timezone.utc)
        if self.last_updated_date and self.last_updated_date >= last_update:
            logging.info("Skipping update of %s, because did not change.", self)
            return False
        else:
            self.last_updated_date = last_update

        self.name = app['name']
        if 'summary' in app:
            self.summary = app['summary']
        if 'description' in app:
            self.description = app['description']
        if 'webSite' in app:
            self.website = app['webSite']
        if 'icon' in app:
            self._update_icon(app['icon'])
        if 'categories' in app:
            self._update_categories(app['categories'])
        if 'added' in app:
            date_added = datetime.datetime.fromtimestamp(app['added'] / 1000, timezone.utc)
            if self.added_date > date_added:
                self.added_date = date_added
        self.save()
        if 'localized' in app:
            self._update_screenshots(app['localized'])
        return True

    def _update_icon(self, icon_name):
        url = self.repo.url + '/icons-640/' + icon_name
        headers = {}
        if self.icon_etag is not None and self.icon_etag != '':
            headers['If-None-Match'] = self.icon_etag
        r = requests.get(url, headers=headers)
        if r.status_code == requests.codes.ok:
            self.delete_old_icon()
            self.icon.save(icon_name, BytesIO(r.content), save=False)
            self.icon_etag = r.headers['ETag']

    def _update_categories(self, categories):
        if not self.pk:
            # we need to save before we can use a ManyToManyField
            self.save()
        for category in categories:
            try:
                cat = Category.objects.get(name=category)
                self.category.add(cat)
            except ObjectDoesNotExist:
                # Drop the unknown category, don't create new categories automatically here
                pass

    def _update_screenshots(self, localized):
        from maker.models import RemoteScreenshot
        package_url = self.repo.url + '/' + self.package_id
        for locale, types in localized.items():
            locale_url = package_url + '/' + locale
            for t, files in types.items():
                type_url = locale_url + '/' + t
                # TODO not only add, but also remove old screenshots again
                RemoteScreenshot.add(locale, t, self, type_url, files)

    def get_latest_apk_pointer(self):
        """
        Returns this app's latest RemoteApkPointer object.
        """
        from .apk import RemoteApkPointer
        return RemoteApkPointer.objects.filter(app=self).order_by('-apk__version_code').all()[0]

    def get_latest_apk(self):
        """
        Returns this app's latest Apk object.
        """
        return self.get_latest_apk_pointer().apk

    def add_to_repo(self, repo):
        """
        Adds this RemoteApp to the given local repository.

        :param repo: The local repository the app should be added to
        :return: The added App object
        """
        from .apk import ApkPointer
        from .screenshot import RemoteScreenshot
        apps = App.objects.filter(repo=repo, package_id=self.package_id)
        if apps.exists():
            raise ValidationError("This app does already exist in your repository.")

        # add app
        app = App.from_remote_app(repo, self)
        app.save()
        app.category = self.category.all()
        app.save()

        # add only latest APK
        remote_pointer = self.get_latest_apk_pointer()
        apk = remote_pointer.apk

        # create a local pointer to the APK
        pointer = ApkPointer(apk=apk, repo=repo, app=app)
        if apk.file:
            pointer.link_file_from_apk()  # this also saves the pointer
        else:
            pointer.save()
            # schedule APK file download if necessary, also updates all local pointers to that APK
            apk.download_async(remote_pointer.url)

        # schedule download of remote screenshots if available
        for remote in RemoteScreenshot.objects.filter(app=self).all():
            remote.download_async(app)

        return app


@receiver(post_delete, sender=App)
def app_post_delete_handler(**kwargs):
    app = kwargs['instance']
    app.delete_old_icon()


@receiver(post_delete, sender=RemoteApp)
def remote_app_post_delete_handler(**kwargs):
    app = kwargs['instance']
    app.delete_old_icon()
