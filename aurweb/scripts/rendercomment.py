#!/usr/bin/env python3

import sys
from urllib.parse import quote_plus
from xml.etree.ElementTree import Element

import bleach
import markdown
import pygit2

import aurweb.config
from aurweb import aur_logging, db, util
from aurweb.models import PackageComment

logger = aur_logging.get_logger(__name__)


class LinkifyExtension(markdown.extensions.Extension):
    """
    Turn URLs into links, even without explicit markdown.
    Do not linkify URLs in code blocks.
    """

    # Captures http(s) and ftp URLs until the first non URL-ish character.
    # Excludes trailing punctuation.
    _urlre = (
        r"(\b(?:https?|ftp):\/\/[\w\/\#~:.?+=&%@!\-;,]+?"
        r"(?=[.:?\-;,]*(?:[^\w\/\#~:.?+=&%@!\-;,]|$)))"
    )

    def extendMarkdown(self, md):
        processor = markdown.inlinepatterns.AutolinkInlineProcessor(self._urlre, md)
        # Register it right after the default <>-link processor (priority 120).
        md.inlinePatterns.register(processor, "linkify", 119)


class FlysprayLinksInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    """
    Turn Flyspray task references like FS#1234 into links to bugs.archlinux.org.

    The pattern's capture group 0 is the text of the link and group 1 is the
    Flyspray task ID.
    """

    def handleMatch(self, m, data):
        el = Element("a")
        el.set("href", f"https://bugs.archlinux.org/task/{m.group(1)}")
        el.text = markdown.util.AtomicString(m.group(0))
        return el, m.start(0), m.end(0)


class FlysprayLinksExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        processor = FlysprayLinksInlineProcessor(r"\bFS#(\d+)\b", md)
        md.inlinePatterns.register(processor, "flyspray-links", 118)


class GitCommitsInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    """
    Turn Git hashes like f7f5152be5ab into links to AUR's cgit.

    Only commit references that do exist are linkified. Hashes are shortened to
    shorter non-ambiguous prefixes. Only hashes with at least 7 digits are
    considered.
    """

    def __init__(self, md, head):
        repo_path = aurweb.config.get("serve", "repo-path")
        self._repo = pygit2.Repository(repo_path)
        self._head = head
        super().__init__(r"\b([0-9a-f]{7,40})\b", md)

    def handleMatch(self, m, data):
        oid = m.group(1)
        # Lookup might raise ValueError in case multiple object ID's were found
        try:
            if oid not in self._repo:
                # Unknown OID; preserve the orginal text.
                return None, None, None
        except ValueError:
            # Multiple OID's found; preserve the orginal text.
            return None, None, None

        el = Element("a")
        commit_uri = aurweb.config.get("options", "commit_uri")
        prefixlen = util.git_search(self._repo, oid)
        el.set(
            "href", commit_uri % (quote_plus(self._head), quote_plus(oid[:prefixlen]))
        )
        el.text = markdown.util.AtomicString(oid[:prefixlen])
        return el, m.start(0), m.end(0)


class GitCommitsExtension(markdown.extensions.Extension):
    _head = None

    def __init__(self, head):
        self._head = head
        super(markdown.extensions.Extension, self).__init__()

    def extendMarkdown(self, md):
        try:
            processor = GitCommitsInlineProcessor(md, self._head)
            md.inlinePatterns.register(processor, "git-commits", 117)
        except pygit2.GitError:
            logger.error("No git repository found for '%s'.", self._head)


class HeadingTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def run(self, doc):
        for elem in doc:
            if elem.tag == "h1":
                elem.tag = "h5"
            elif elem.tag in ["h2", "h3", "h4", "h5"]:
                elem.tag = "h6"


class HeadingExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        # Priority doesn't matter since we don't conflict with other processors.
        md.treeprocessors.register(HeadingTreeprocessor(md), "heading", 30)


class StrikethroughInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    def handleMatch(self, m, data):
        el = Element("del")
        el.text = m.group(1)
        return el, m.start(0), m.end(0)


class StrikethroughExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        pattern = r"~~(.*?)~~"
        processor = StrikethroughInlineProcessor(pattern, md)
        md.inlinePatterns.register(processor, "del", 40)


def save_rendered_comment(comment: PackageComment, html: str):
    with db.begin():
        comment.RenderedComment = html


def update_comment_render_fastapi(comment: PackageComment) -> None:
    update_comment_render(comment)


def update_comment_render(comment: PackageComment) -> None:
    text = comment.Comments
    pkgbasename = comment.PackageBase.Name

    html = markdown.markdown(
        text,
        extensions=[
            "md_in_html",
            "fenced_code",
            LinkifyExtension(),
            FlysprayLinksExtension(),
            GitCommitsExtension(pkgbasename),
            HeadingExtension(),
            StrikethroughExtension(),
        ],
    )

    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        "p",
        "pre",
        "h4",
        "h5",
        "h6",
        "br",
        "hr",
        "del",
        "details",
        "summary",
    ]
    html = bleach.clean(html, tags=allowed_tags)
    save_rendered_comment(comment, html)
    db.refresh(comment)


def main() -> None:
    db.get_engine()
    comment_id = int(sys.argv[1])
    comment = db.query(PackageComment).filter(PackageComment.ID == comment_id).first()
    update_comment_render(comment)


if __name__ == "__main__":
    main()
