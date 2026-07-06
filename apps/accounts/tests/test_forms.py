import pytest

from apps.accounts.forms import CustomUserCreationForm
from apps.accounts.models import User


@pytest.mark.django_db
def test_creates_custom_user_model():
    """Regression test for the 'Manager isn't available; auth.User has been
    swapped for accounts.User' bug: the form must target the swapped-in
    custom User model, not django.contrib.auth's stock one."""
    form = CustomUserCreationForm(data={
        'username': 'newperson',
        'password1': 'a-strong-password-1',
        'password2': 'a-strong-password-1',
    })
    assert form.is_valid(), form.errors

    user = form.save()

    assert isinstance(user, User)
    assert User.objects.filter(username='newperson').exists()
