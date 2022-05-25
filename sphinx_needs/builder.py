import os
from typing import Iterable, Optional, Set

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.builders import Builder

from sphinx_needs.logging import get_logger
from sphinx_needs.needsfile import NeedsList

log = get_logger(__name__)


class NeedsBuilder(Builder):
    name = "needs"
    format = "json"
    file_suffix = ".txt"
    links_suffix = None

    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        pass

    def finish(self) -> None:
        needs = self.env.needs_all_needs.values()  # We need a list of needs for later filter checks
        filters = self.env.needs_all_filters
        config = self.env.config
        version = getattr(config, "version", "unset")
        needs_list = NeedsList(config, self.outdir, self.confdir)

        if config.needs_file:
            needs_file = config.needs_file
            needs_list.load_json(needs_file)
        else:
            # check if needs.json file exists in conf.py directory
            needs_json = os.path.join(self.confdir, "needs.json")
            if os.path.exists(needs_json):
                log.info("needs.json found, but will not be used because needs_file not configured.")

        # Clean needs_list from already stored needs of the current version.
        # This is needed as needs could have been removed from documentation and if this is the case,
        # removed needs would stay in needs_list, if list gets not cleaned.
        needs_list.wipe_version(version)
        #
        from sphinx_needs.filter_common import filter_needs

        filter_string = self.app.config.needs_builder_filter
        filtered_needs = filter_needs(self.app, needs, filter_string)

        for need in filtered_needs:
            needs_list.add_need(version, need)

        for need_filter in filters.values():
            if need_filter["export_id"]:
                needs_list.add_filter(version, need_filter)

        try:
            needs_list.write_json()
        except Exception as e:
            log.error(f"Error during writing json file: {e}")
        else:
            log.info("Needs successfully exported")

    def get_outdated_docs(self) -> Iterable[str]:
        return []

    def prepare_writing(self, docnames: Set[str]) -> None:
        pass

    def write_doc_serialized(self, docname: str, doctree: nodes.document) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def get_target_uri(self, docname: str, typ: Optional[str] = None) -> str:
        return ""


def build_needs_json(app: Sphinx, exception) -> None:

    if not app.env.config.needs_build_json:
        return

    # Do not create an additional needs.json, if builder is already "needs".
    if isinstance(app.builder, NeedsBuilder):
        return

    needs_builder = NeedsBuilder(app)
    needs_builder.set_environment(app.env)
    needs_builder.finish()