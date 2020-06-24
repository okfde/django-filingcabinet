from django import forms

DEFAULT_PREFERENCES = {
    "showToolbar": True,
    "showTextToggle": True,
    "showZoom": True,
    "showSearch": True,
    "showSidebarToggle": True,
    "showOutlineToggle": 'unknown',
    "showAnnotationsToggle": 'unknown',
    "showText": '',
    "showSidebar": True,
    "showOutline": '',
    "showAnnotations": '',
    "defaultSearch": '',
    "defaultZoom": 1,
    "showPageNumberInput": True
}


def get_viewer_preferences(input_data):
    preferences = dict(DEFAULT_PREFERENCES)
    preferences.update(input_data)
    form = ViewerPreferenceForm(data=preferences)
    if form.is_valid():
        return {
            k: v for k, v in form.cleaned_data.items()
            if v is not None
        }


class ViewerPreferenceForm(forms.Form):
    showToolbar = forms.BooleanField(
        required=False
    )
    showTextToggle = forms.BooleanField(
        required=False
    )
    showZoom = forms.BooleanField(
        required=False
    )
    showSearch = forms.BooleanField(
        required=False
    )
    showSidebarToggle = forms.BooleanField(
        required=False
    )
    showOutlineToggle = forms.NullBooleanField(
        required=False
    )
    showAnnotationsToggle = forms.NullBooleanField(
        initial='1', required=False
    )
    showText = forms.BooleanField(
        initial=False, required=False
    )
    showSidebar = forms.BooleanField(
        required=False
    )
    showOutline = forms.BooleanField(
        initial=False, required=False
    )
    showAnnotations = forms.BooleanField(
        initial=False, required=False
    )
    showPageNumberInput = forms.BooleanField(
        required=False
    )
    defaultSearch = forms.CharField(required=False)
    defaultZoom = forms.IntegerField(min_value=1, max_value=3)
