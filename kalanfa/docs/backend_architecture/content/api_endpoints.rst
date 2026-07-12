API endpoints
-------------

URL Namespacing
~~~~~~~~~~~~~~~

Kalanfa uses a consistent URL namespacing pattern throughout the codebase. All URLs follow the format:

    >>> kalanfa:<plugin_module>:<url_name>

Where ``<plugin_module>`` is either ``core`` for core Kalanfa functionality (a special case, as core is not actually in a plugin module), or the full plugin module path (e.g., ``kalanfa.plugins.coach``) for plugins.

For example:

    >>> kalanfa:core:session_list
    >>> kalanfa:core:session_detail
    >>> kalanfa:core:usernameavailable
    >>> kalanfa:kalanfa.plugins.coach:lessonreport_list
    >>> kalanfa:kalanfa.plugins.coach:lessonreport_detail

This namespacing is used both in Django backend URL configuration and in JavaScript frontend code.

For comprehensive information about URL namespacing, including how to define and use URLs in both backend and frontend code, see the :doc:`/howtos/working_with_urls_and_api_endpoints` guide.

Example Endpoints
~~~~~~~~~~~~~~~~~

request specific content:

    >>> localhost:8000/api/content/<channel_id>/contentnode/<content_id>

search content:

    >>> localhost:8000/api/content/<channel_id>/contentnode/?search=<search words>

request specific content with specified fields:

    >>> localhost:8000/api/content/<channel_id>/contentnode/<content_id>/?fields=pk,title,kind

request paginated contents

    >>> localhost:8000/api/content/<channel_id>/contentnode/?page=6&page_size=10

request combines different usages

    >>> localhost:8000/api/content/<channel_id>/contentnode/?fields=pk,title,kind,instance_id,description,files&page=6&page_size=10&search=wh
