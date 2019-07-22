from django import forms
from django.forms.models import inlineformset_factory
from django.forms.models import BaseInlineFormSet

from ..models import EnginePatch, Engine


class EnginePatchForm(forms.ModelForm):

    class Meta:
        model = EnginePatch
        fields = ('patch_version', 'is_initial_patch', 'patch_path')


class EnginePatchFormset(BaseInlineFormSet):

    def clean(self):
        """This method validates duplicated initial_patch given for an
        EnginePatch formset. ValidationError is not triggered when an objects
        is being deleted.
        """
        super(EnginePatchFormset, self).clean()

        count = 0
        for form in self.forms:
            cleaned_data = form.cleaned_data
            if cleaned_data and cleaned_data.get('is_initial_patch'):
                if not cleaned_data.get('DELETE'):
                    count += 1
        if count == 0:
            raise forms.ValidationError(
                'You must select at least one initial_patch'
            )
        if count > 1:
            raise forms.ValidationError('You must have only one initial_patch')


engine_patch_formset = inlineformset_factory(
    Engine,
    EnginePatch,
    form=EnginePatchForm,
    formset=EnginePatchFormset
)
