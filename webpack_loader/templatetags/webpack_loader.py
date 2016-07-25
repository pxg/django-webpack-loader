from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from ..utils import get_loader
from ..exceptions import WebpackLoaderBadStatsError

register = template.Library()


def filter_by_extension(bundle, extension):
    '''Return only files with the given extension'''
    for chunk in bundle:
        if chunk['name'].endswith('.{0}'.format(extension)):
            yield chunk


def render_as_tags(bundle, attrs):
    tags = []
    for chunk in bundle:
        if chunk['name'].endswith('.js'):
            tags.append((
                '<script type="text/javascript" src="{0}" {1}></script>'
            ).format(chunk['url'], attrs))
        elif chunk['name'].endswith('.css'):
            tags.append((
                '<link type="text/css" href="{0}" rel="stylesheet" {1}/>'
            ).format(chunk['url'], attrs))
    return mark_safe('\n'.join(tags))


def _get_bundle(bundle_name, extension, config):
    bundle = get_loader(config).get_bundle(bundle_name)
    if extension:
        bundle = filter_by_extension(bundle, extension)
    return bundle


@register.simple_tag
def render_bundle(bundle_name, extension=None, config='DEFAULT', attrs=''):
    '''
    If there's a problem with the Webpack stats file serve a fallback css file
    This is to prevent 500 errors on deployment
    '''
    try:
        result = render_as_tags(
            _get_bundle(bundle_name, extension, config), attrs)
        return result
    except WebpackLoaderBadStatsError:
        url = 'https://dr2d0q0030ozz.cloudfront.net/main-41f2dc17fac5aad4a382.css'
        return '<link type="text/css" href="{}" rel="stylesheet" />'.format(url)


@register.simple_tag
def webpack_static(asset_name, config='DEFAULT'):
    return "{0}{1}".format(
        get_loader(config).get_assets().get(
            'publicPath', getattr(settings, 'STATIC_URL')
        ),
        asset_name
    )


@register.assignment_tag
def get_files(bundle_name, extension=None, config='DEFAULT'):
    """
    Returns all chunks in the given bundle.
    Example usage::

        {% get_files 'editor' 'css' as editor_css_chunks %}
        CKEDITOR.config.contentsCss = '{{ editor_css_chunks.0.publicPath }}';

    :param bundle_name: The name of the bundle
    :param extension: (optional) filter by extension
    :param config: (optional) the name of the configuration
    :return: a list of matching chunks
    """
    return list(_get_bundle(bundle_name, extension, config))
