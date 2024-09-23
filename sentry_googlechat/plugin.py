from __future__ import absolute_import

from sentry import tagstore
from sentry.plugins.bases import notify
from sentry.utils import json
from sentry.http import safe_urlopen
from sentry.integrations.base import FeatureDescription, IntegrationFeatures
from sentry_plugins.base import CorePluginMixin

from . import __version__, __doc__ as package_doc

class GoogleChatPlugin(CorePluginMixin, notify.NotificationPlugin):
    description = package_doc
    version = __version__
    title = 'Google Chat'
    slug = 'googlechat'
    conf_key = 'googlechat'
    conf_title = title
    author = 'Jonhnny Weslley'
    author_url = 'https://jonhnnyweslley.net/'
    resource_links = (
        ('Bug Tracker', 'https://github.com/jweslley/sentry-googlechat/issues'),
        ('Source', 'https://github.com/jweslley/sentry-googlechat'),
    )
    required_field = "webhook"
    feature_descriptions = [
        FeatureDescription(
            """
            Configure Sentry rules to trigger notifications based on conditions you set.
            """,
            IntegrationFeatures.ALERT_RULE,
        )
    ]

    def is_configured(self, project):
        return bool(self.get_option('webhook', project))

    def get_config(self, project, **kwargs):
        return [
            {
                'name': 'webhook',
                'label': 'Google Chat Webhook URL',
                'type': 'url',
                'placeholder': 'e.g. https://chat.googleapis.com/v1/spaces/ABCDEF123/messages?key=abcde-12345-5555-1111-eeee&token=abcdef12345678',
                'required': True,
                'help': 'Google Chat Incoming Webhook URL'
            },
            {
                "name": "include_tags",
                "label": "Include Tags",
                "type": "bool",
                "required": False,
                "help": "Include tags with notifications",
            },
            {
                "name": "included_tag_keys",
                "label": "Included Tags",
                "type": "string",
                "required": False,
                "help": (
                    "Only include these tags (comma separated list). " "Leave empty to include all."
                ),
            },
            {
                "name": "excluded_tag_keys",
                "label": "Excluded Tags",
                "type": "string",
                "required": False,
                "help": "Exclude these tags (comma separated list).",
            },
            {
                "name": "exclude_project",
                "label": "Exclude Project Name",
                "type": "bool",
                "default": False,
                "required": False,
                "help": "Exclude project name with notifications.",
            },
            {
                "name": "exclude_culprit",
                "label": "Exclude Culprit",
                "type": "bool",
                "default": False,
                "required": False,
                "help": "Exclude culprit with notifications.",
            },
        ]

    def get_tag_list(self, name, project):
        option = self.get_option(name, project)
        if not option:
            return None
        return set(tag.strip().lower() for tag in option.split(","))

    def _get_tags(self, event):
        tag_list = event.tags
        if not tag_list:
            return ()

        return (
            (tagstore.get_tag_key_label(k), tagstore.get_tag_value_label(k, v)) for k, v in tag_list
        )

    def build_tags_widget(self, project, event):
        if not self.get_option("include_tags", project):
            return None

        tags = []
        included_tags = set(self.get_tag_list("included_tag_keys", project) or [])
        excluded_tags = set(self.get_tag_list("excluded_tag_keys", project) or [])
        for tag_key, tag_value in self._get_tags(event):
            key = tag_key.lower()
            std_key = tagstore.get_standardized_key(key)
            if included_tags and key not in included_tags and std_key not in included_tags:
                continue
            if excluded_tags and (key in excluded_tags or std_key in excluded_tags):
                continue

            tags.append({ "keyValue": { "topLabel": tag_key.encode("utf-8"), "content": tag_value.encode("utf-8") }})
        return tags

    def notify(self, notification, raise_exception=False):
        event = notification.event
        group = event.group
        project = group.project

        if not self.is_configured(project):
            return

        event_title = event.title.encode('utf-8')
        event_message = event.message.encode('utf-8')

        project_name = project.get_full_name().encode('utf-8')
        if group.culprit:
            culprit = group.culprit.encode("utf-8")
        else:
            culprit = None

        sections = []
        widgets = []
        if not self.get_option("exclude_project", project):
            widgets.append({ "keyValue": { "topLabel": "Project", "content": project_name }})

        if not self.get_option("exclude_culprit", project) and culprit and event_title != culprit:
            widgets.append({ "keyValue": { "topLabel": "Culprit", "content": culprit }})

        times_seen = 'Seen %s times' % group.times_seen
        first_seen = 'First seen %s' % group.first_seen.strftime("%b %d, %Y %H:%M:%S %p %Z")
        widgets.append({ "keyValue": { "topLabel": "Times Seen", "content": times_seen,
                                      "bottomLabel": first_seen }})

        sections.append({ "widgets": widgets })

        tags = self.build_tags_widget(project, event)
        if tags:
            sections.append({ "header": "Tags", "widgets": tags })

        url = group.get_absolute_url()
        buttons = {"buttons": [{"textButton": {"text": "OPEN IN SENTRY",
                                               "onClick": {"openLink": { "url": url }}}}]}
        sections.append({ "widgets": buttons })

        title = '[%s] %s' % (project_name, event_title)
        payload = {"cards": [
            { "header": { "title": title, "subtitle": event_message },
             "sections": sections } ]}

        webhook = self.get_option('webhook', project)
        return safe_urlopen(webhook, method='POST', data=json.dumps(payload))
