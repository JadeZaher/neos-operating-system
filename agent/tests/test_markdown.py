"""Tests for the server-side markdown rendering utility."""

from markupsafe import Markup

from neos_agent.views._rendering import render_markdown


class TestRenderMarkdown:
    """render_markdown: mistune + nh3 pipeline."""

    # -- basic rendering --

    def test_heading(self):
        result = render_markdown("# Hello")
        assert "<h1>" in result
        assert "Hello" in result

    def test_bold_and_italic(self):
        result = render_markdown("**bold** and *italic*")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_unordered_list(self):
        result = render_markdown("- one\n- two")
        assert "<ul>" in result
        assert "<li>" in result

    def test_ordered_list(self):
        result = render_markdown("1. first\n2. second")
        assert "<ol>" in result

    def test_link(self):
        result = render_markdown("[example](https://example.com)")
        assert 'href="https://example.com"' in result
        assert "example" in result

    def test_code_block(self):
        result = render_markdown("```python\nprint('hi')\n```")
        assert "<pre>" in result
        assert "<code" in result

    def test_inline_code(self):
        result = render_markdown("use `foo()` here")
        assert "<code>" in result
        assert "foo()" in result

    def test_blockquote(self):
        result = render_markdown("> quote")
        assert "<blockquote>" in result

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = render_markdown(md)
        assert "<table>" in result
        assert "<td>" in result

    def test_strikethrough(self):
        result = render_markdown("~~deleted~~")
        assert "<del>" in result

    # -- empty / None --

    def test_none_returns_empty_markup(self):
        result = render_markdown(None)
        assert result == ""
        assert isinstance(result, Markup)

    def test_empty_string_returns_empty_markup(self):
        result = render_markdown("")
        assert result == ""
        assert isinstance(result, Markup)

    # -- returns Markup (safe for Jinja2) --

    def test_returns_markup_type(self):
        result = render_markdown("hello")
        assert isinstance(result, Markup)

    # -- XSS / sanitisation --

    def test_script_tag_neutralised(self):
        result = render_markdown("<script>alert(1)</script>")
        # Raw <script> tag must not appear — escaped to &lt;script&gt; is safe
        assert "<script>" not in result

    def test_onerror_neutralised(self):
        result = render_markdown('<img src=x onerror="alert(1)">')
        # Must not produce an actual img with onerror handler — escaped is safe
        assert "<img" not in result or "onerror" not in result

    def test_javascript_url_stripped(self):
        result = render_markdown("[click](javascript:alert(1))")
        assert "javascript:" not in result

    def test_style_tag_stripped(self):
        result = render_markdown("<style>body{display:none}</style>")
        assert "<style>" not in result

    def test_iframe_stripped(self):
        result = render_markdown("<iframe src='https://evil.com'></iframe>")
        assert "<iframe>" not in result

    # -- link safety --

    def test_links_get_rel_attribute(self):
        result = render_markdown("[x](https://example.com)")
        assert "noopener" in result
        assert "noreferrer" in result
        assert "nofollow" in result
