"""
Template Variables
"""

from datetime import datetime

from tkai import __version__


def build_variables(
    project_name: str,
    template: str,
 ) -> dict[str, str]:
    """Build the standard variables available to legacy templates."""
    return {

        "project_name": project_name,

        "package_name": project_name.lower(),

        "template": template,

        "author": "TKAI",

        "year": str(datetime.now().year),

        "python_version": "3.14",

        "tkai_version": __version__,

    }
