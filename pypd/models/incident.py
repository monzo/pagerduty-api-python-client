# Copyright (c) PagerDuty.
# See LICENSE for details.
import json

import six

from .entity import Entity
from .log_entry import LogEntry
from .note import Note
from .alert import Alert
from ..errors import InvalidArguments, MissingFromEmail


class Incident(Entity):
    """Represents an Incident in PagerDuty's API."""

    STR_OUTPUT_FIELDS = ('id', 'status',)

    logEntryFactory = LogEntry
    noteFactory = Note
    alertFactory = Alert

    def resolve(self, from_email, resolution=None):
        """Resolve an incident using a valid email address."""
        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        endpoint = '/'.join((self.endpoint, self.id,))
        add_headers = {'from': from_email, }
        data = {
            'incident': {
                'type': 'incident',
                'status': 'resolved',
            }
        }

        if resolution is not None:
            data['resolution'] = resolution

        result = self.request('PUT',
                              endpoint=endpoint,
                              add_headers=add_headers,
                              data=data,)
        return result

    def acknowledge(self, from_email):
        """Resolve an incident using a valid email address."""
        endpoint = '/'.join((self.endpoint, self.id,))

        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        add_headers = {'from': from_email, }
        data = {
            'incident': {
                'type': 'incident',
                'status': 'acknowledged',
            }
        }

        result = self.request('PUT',
                              endpoint=endpoint,
                              add_headers=add_headers,
                              data=data,)
        return result

    def reassign(self, from_email, user_ids):
        """Reassign an incident to other users using a valid email address."""
        endpoint = '/'.join((self.endpoint, self.id,))

        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        if user_ids is None or not isinstance(user_ids, list):
            raise InvalidArguments(user_ids)
        if not all([isinstance(i, six.string_types) for i in user_ids]):
            raise InvalidArguments(user_ids)

        assignees = [
            {
                'assignee': {
                    'id': user_id,
                    'type': 'user_reference',
                }
            }
            for user_id in user_ids
        ]

        add_headers = {'from': from_email, }
        data = {
            'incident': {
                'type': 'incident',
                'assignments': assignees,
            }
        }

        result = self.request('PUT',
                              endpoint=endpoint,
                              add_headers=add_headers,
                              data=data,)
        return result

    def add_responders(self, from_email, requester_id, message, user_ids=None, escalation_policy_ids=None):
        """Request responders to join an incident using a valid email address."""
        endpoint = '/'.join((self.endpoint, self.id, 'responder_requests'))

        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        if not (user_ids or escalation_policy_ids):
            raise InvalidArguments('Need at least one target to be supplied')

        responders = []

        if user_ids:
            if not isinstance(user_ids, list):
                raise InvalidArguments(user_ids)
            if not all([isinstance(i, six.string_types) for i in user_ids]):
                raise InvalidArguments(user_ids)

            users = [
                {
                    'responder_request_target': {
                        'id': user_id,
                        'type': 'user_reference',
                    }
                }
                for user_id in user_ids
            ]
            responders += users

        if escalation_policy_ids:
            if not isinstance(escalation_policy_ids, list):
                raise InvalidArguments(escalation_policy_ids)
            if not all([isinstance(i, six.string_types) for i in escalation_policy_ids]):
                raise InvalidArguments(escalation_policy_ids)

            esclation_policies = [
                {
                    'responder_request_target': {
                        'id': escalation_policy_id,
                        'type': 'escalation_policy_reference',
                    }
                }
                for escalation_policy_id in escalation_policy_ids
            ]
            responders += esclation_policies

        add_headers = {'from': from_email, }
        data = {
            'requester_id': requester_id,
            "message": message,
            "responder_request_targets": responders
        }

        result = self.request('POST',
                              endpoint=endpoint,
                              add_headers=add_headers,
                              data=data,)
        return result

    def reassign_escalation_policy(self, from_email, escalation_policy_id):
        """Reassign an incident to another escalation policy using a valid email address."""
        endpoint = '/'.join((self.endpoint, self.id,))

        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        if escalation_policy_id is None or not isinstance(escalation_policy_id, six.string_types):
            raise InvalidArguments(escalation_policy_id)

        add_headers = {'from': from_email, }
        data = {
            'incident': {
                'type': 'incident',
                'escalation_policy': {
                    'id': escalation_policy_id,
                    'type': 'escalation_policy_reference',
                },
            }
        }

        result = self.request('PUT',
                              endpoint=endpoint,
                              add_headers=add_headers,
                              data=data,)
        return result

    def rename(self, from_email, title):
        """Rename an incident using a valid email address."""
        endpoint = '/'.join((self.endpoint, self.id,))

        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        if title is None or not isinstance(title, six.string_types):
            raise InvalidArguments(title)

        add_headers = {'from': from_email, }
        data = {
            'incident': {
                'type': 'incident',
                'title': title,
            }
        }

        result = self.request('PUT',
                              endpoint=endpoint,
                              add_headers=add_headers,
                              data=data,)
        return result

    def log_entries(self, time_zone='UTC', is_overview=False,
                    include=None, fetch_all=True):
        """Query for log entries on an incident instance."""
        endpoint = '/'.join((self.endpoint, self.id, 'log_entries'))

        query_params = {
            'time_zone': time_zone,
            'is_overview': json.dumps(is_overview),
        }

        if include:
            query_params['include'] = include

        result = self.logEntryFactory.find(
            endpoint=endpoint,
            api_key=self.api_key,
            fetch_all=fetch_all,
            **query_params
        )

        return result

    def update(self, *args, **kwargs):
        """Update this incident."""
        raise NotImplemented

    def notes(self):
        """Query for notes attached to this incident."""
        endpoint = '/'.join((self.endpoint, self.id, 'notes'))
        return self.noteFactory.find(
            endpoint=endpoint,
            api_key=self.api_key,
        )

    def create_note(self, from_email, content):
        """Create a note for this incident."""
        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        endpoint = '/'.join((self.endpoint, self.id, 'notes'))
        add_headers = {'from': from_email, }

        return self.noteFactory.create(
            endpoint=endpoint,
            api_key=self.api_key,
            add_headers=add_headers,
            data={'content': content},
        )

    def snooze(self, from_email, duration):
        """Snooze this incident for `duration` seconds."""
        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        endpoint = '/'.join((self.endpoint, self.id, 'snooze'))
        add_headers = {'from': from_email, }

        return self.__class__.create(
            endpoint=endpoint,
            api_key=self.api_key,
            add_headers=add_headers,
            data_key='duration',
            data=duration,
        )

    def merge(self, from_email, source_incidents):
        """Merge other incidents into this incident."""
        if from_email is None or not isinstance(from_email, six.string_types):
            raise MissingFromEmail(from_email)

        add_headers = {'from': from_email, }
        endpoint = '/'.join((self.endpoint, self.id, 'merge'))
        incident_ids = [entity['id'] if isinstance(entity, Entity) else entity
                        for entity in source_incidents]
        incident_references = [{'type': 'incident_reference', 'id': id_}
                               for id_ in incident_ids]

        return self.__class__.create(
            endpoint=endpoint,
            api_key=self.api_key,
            add_headers=add_headers,
            data_key='source_incidents',
            data=incident_references,
            method='PUT',
        )

    def alerts(self):
        """Query for alerts attached to this incident."""
        endpoint = '/'.join((self.endpoint, self.id, 'alerts'))
        return self.alertFactory.find(
            endpoint=endpoint,
            api_key=self.api_key,
        )
