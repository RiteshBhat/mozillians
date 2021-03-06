from mock import patch
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from funfactory.helpers import urlparams
from mozillians.common.tests import TestCase
from mozillians.phonebook.tests import InviteFactory
from mozillians.phonebook.utils import update_invites
from mozillians.users.tests import UserFactory
from nose.tools import eq_, ok_


class RegisterTests(TestCase):
    def test_register_anonymous(self):
        client = Client()
        url = urlparams(reverse('phonebook:register'), code='foo')
        response = client.get(url, follow=True)
        eq_(client.session['invite-code'], 'foo')
        self.assertTemplateUsed(response, 'phonebook/home.html')

    @patch('mozillians.phonebook.views.update_invites',
           wraps=update_invites)
    def test_register_unvouched(self, update_invites_mock):
        user = UserFactory.create()
        invite = InviteFactory.create(inviter=user.userprofile)
        url = urlparams(reverse('phonebook:register'), code=invite.code)
        with self.login(user) as client:
            response = client.get(url, follow=True)
        user = User.objects.get(id=user.id)
        ok_(user.userprofile.is_vouched)
        ok_(update_invites_mock.called)
        self.assertTemplateUsed(response, 'phonebook/home.html')

    @patch('mozillians.phonebook.views.update_invites',
           wraps=update_invites)
    def test_register_vouched(self, update_invites_mock):
        voucher_1 = UserFactory.create(userprofile={'is_vouched': True})
        voucher_2 = UserFactory.create(userprofile={'is_vouched': True})
        user = UserFactory.create(
            userprofile={'is_vouched': True,
                         'vouched_by': voucher_1.userprofile})
        invite = InviteFactory.create(inviter=voucher_2.userprofile)
        url = urlparams(reverse('phonebook:register'), code=invite.code)
        with self.login(user) as client:
            response = client.get(url, follow=True)
        user = User.objects.get(id=user.id)
        ok_(user.userprofile.is_vouched)
        ok_(user.userprofile.vouched_by, voucher_1.userprofile)
        ok_(not update_invites_mock.called)
        self.assertTemplateUsed(response, 'phonebook/home.html')

    def test_register_without_code_anonymous(self):
        client = Client()
        response = client.get(reverse('phonebook:register'), follow=True)
        ok_(not self.client.session.get('invite-code'))
        self.assertTemplateUsed(response, 'phonebook/home.html')
        eq_(response.status_code, 200)

    def test_register_without_code_unvouched(self):
        user = UserFactory.create()
        with self.login(user) as client:
            response = client.get(reverse('phonebook:register'), follow=True)
        ok_(not self.client.session.get('invite-code'))
        self.assertTemplateUsed(response, 'phonebook/home.html')
        eq_(response.status_code, 200)

    def test_register_without_code_vouched(self):
        user = UserFactory.create(userprofile={'is_vouched': True})
        with self.login(user) as client:
            response = client.get(reverse('phonebook:register'), follow=True)
        ok_(not self.client.session.get('invite-code'))
        self.assertTemplateUsed(response, 'phonebook/home.html')
        eq_(response.status_code, 200)
