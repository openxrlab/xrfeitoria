from typing import Any, Dict, List, Optional, Tuple

import sphinx
from docutils.nodes import Node
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.ext.graphviz import figure_wrapper
from sphinx.ext.inheritance_diagram import (
    InheritanceDiagram,
    InheritanceException,
    InheritanceGraph,
    inheritance_diagram,
    py_builtins,
)
from sphinx.util.typing import OptionSpec

# sphinx==7.2.5


class CustomInheratanceGraph(InheritanceGraph):
    def __init__(
        self,
        class_names: List[str],
        currmodule: str,
        show_builtins: bool = False,
        private_bases: bool = False,
        parts: int = 0,
        aliases: Optional[Dict[str, str]] = None,
        top_classes: List[Any] = [],
        skip_classes: List[Any] = [],
    ) -> None:
        self.skip_classes = skip_classes
        super().__init__(class_names, currmodule, show_builtins, private_bases, parts, aliases, top_classes)

    def _class_info(
        self,
        classes: List[Any],
        show_builtins: bool,
        private_bases: bool,
        parts: int,
        aliases: Dict[str, str],
        top_classes: List[Any],
    ) -> List[Tuple[str, str, List[str], str]]:
        """Return name and bases for all classes that are ancestors of *classes*.

        *parts* gives the number of dotted name parts to include in the
        displayed node names, from right to left. If given as a negative, the
        number of parts to drop from the left. A value of 0 displays the full
        dotted name. E.g. ``sphinx.ext.inheritance_diagram.InheritanceGraph``
        with ``parts=2`` or ``parts=-2`` gets displayed as
        ``inheritance_diagram.InheritanceGraph``, and as
        ``ext.inheritance_diagram.InheritanceGraph`` with ``parts=3`` or
        ``parts=-1``.

        *top_classes* gives the name(s) of the top most ancestor class to
        traverse to. Multiple names can be specified separated by comma.
        """
        all_classes = {}

        def recurse(cls: Any) -> None:
            if not show_builtins and cls in py_builtins:
                return
            if not private_bases and cls.__name__.startswith('_'):
                return

            nodename = self.class_name(cls, parts, aliases)
            fullname = self.class_name(cls, 0, aliases)

            # Skip classes pre-defined in the options
            if fullname in self.skip_classes:
                return

            # Use first line of docstring as tooltip, if available
            tooltip = None
            try:
                if cls.__doc__:
                    doc = cls.__doc__.strip().split('\n')[0]
                    if doc:
                        tooltip = '"%s"' % doc.replace('"', '\\"')
            except Exception:  # might raise AttributeError for strange classes
                pass

            baselist: List[str] = []
            all_classes[cls] = (nodename, fullname, baselist, tooltip)

            if fullname in top_classes:
                return

            for base in cls.__bases__:
                if not show_builtins and base in py_builtins:
                    continue
                if not private_bases and base.__name__.startswith('_'):
                    continue

                # Skip classes pre-defined in the options
                nodename = self.class_name(base, parts, aliases)
                fullname = self.class_name(base, 0, aliases)
                if fullname in self.skip_classes:
                    continue

                baselist.append(nodename)
                if base not in all_classes:
                    recurse(base)

        for cls in classes:
            recurse(cls)

        return list(all_classes.values())


class CustomInheritanceDiagram(InheritanceDiagram):
    """Run when the inheritance_diagram directive is first encountered."""

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: OptionSpec = {
        'parts': int,
        'private-bases': directives.flag,
        'caption': directives.unchanged,
        'top-classes': directives.unchanged_required,
        'skip-classes': directives.unchanged_required,
        'align': lambda arg: directives.choice(arg, ('left', 'center', 'right')),
    }

    def run(self) -> List[Node]:
        node = inheritance_diagram()
        node.document = self.state.document
        class_names = self.arguments[0].split()
        class_role = self.env.get_domain('py').role('class')
        # Store the original content for use as a hash
        node['parts'] = self.options.get('parts', 0)
        node['content'] = ', '.join(class_names)
        node['top-classes'] = []
        if 'align' in self.options:
            node['align'] = self.options['align']
        for cls in self.options.get('top-classes', '').split(','):
            cls = cls.strip()
            if cls:
                node['top-classes'].append(cls)

        # Create a graph starting with the list of classes
        try:
            graph = CustomInheratanceGraph(
                class_names,
                self.env.ref_context.get('py:module'),
                parts=node['parts'],
                private_bases='private-bases' in self.options,
                aliases=self.config.inheritance_alias,
                top_classes=node['top-classes'],
                skip_classes=self.options.get('skip-classes', '').split(','),
            )
        except InheritanceException as err:
            return [node.document.reporter.warning(err, line=self.lineno)]

        if len(graph.get_all_class_names()) <= 1:
            return [
                node.document.reporter.warning(
                    'skip inheritance diagram for no parent class',
                    line=self.lineno,
                )
            ]

        # Create xref nodes for each target of the graph's image map and
        # add them to the doc tree so that Sphinx can resolve the
        # references to real URLs later.  These nodes will eventually be
        # removed from the doctree after we're done with them.
        for name in graph.get_all_class_names():
            refnodes, x = class_role(  # type: ignore
                'class', ':class:`%s`' % name, name, 0, self.state
            )  # type: ignore
            node.extend(refnodes)
        # Store the graph object so we can use it to generate the
        # dot file later
        node['graph'] = graph
        if 'caption' not in self.options:
            self.add_name(node)
            return [node]
        else:
            figure = figure_wrapper(self, node, self.options['caption'])
            self.add_name(figure)
            return [figure]


def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension('sphinx.ext.graphviz')
    app.add_directive('custom-inheritance-diagram', CustomInheritanceDiagram)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
