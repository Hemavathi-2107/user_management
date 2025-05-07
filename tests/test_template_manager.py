import pytest
from markdown2 import markdown
import importlib

import settings.config as config
import app.utils.template_manager as tm_module

class DummyTM(tm_module.TemplateManager):
    """Subclass so we can override where templates come from."""
    def __init__(self, templates):
        # skip real filesystem setup
        self.templates = templates

    def _read_template(self, filename: str) -> str:
        # Return from our in-memory dict
        try:
            return self.templates[filename]
        except KeyError:
            raise FileNotFoundError(f"No such template: {filename}")

@pytest.fixture
def basic_templates():
    return {
        "header.md": "# Welcome!",
        "footer.md": "*Thank you for reading.*",
        "greet.md": "Hello, **{name}**!"
    }

@pytest.fixture
def manager(basic_templates):
    return DummyTM(basic_templates)


def test_read_template_missing_file(manager):
    with pytest.raises(FileNotFoundError):
        manager._read_template("does_not_exist.md")


def test_apply_email_styles_inlines_all_tags():
    html = "<h1>Title</h1><p>Paragraph</p><a>Link</a><ul><li>Item</li></ul><footer>Foot</footer>"
    styled = tm_module.TemplateManager()._apply_email_styles(html)
    # Body wrapper
    assert styled.startswith('<div style="font-family: Arial')
    # Each tag has inline style attribute
    assert '<h1 style="font-size: 24px;' in styled
    assert '<p style="font-size: 16px;' in styled
    assert '<a style="color: #0056b3;' in styled
    assert '<ul style="list-style-type: none;' in styled
    assert '<li style="margin-bottom: 10px;' in styled
    assert '<footer style="font-size: 12px;' in styled


def test_render_template_combines_and_renders(manager):
    # Render greet.md with context
    output = manager.render_template("greet", name="Alice")

    # Underlying markdown would become:
    # "# Welcome!\nHello, **Alice**!\n*Thank you for reading.*"
    # After markdown2 markdown, it contains <h1>, <p>, <strong> etc
    assert "<h1" in output  # from header
    assert "Welcome!" in output
    assert "<strong>Alice</strong>" in output  # bold from greet
    assert "Thank you for reading." in output  # from footer

    # And all tags must have been inlined
    assert 'style="font-family: Arial' in output  # wrapper
    assert '<h1 style="' in output
    assert '<p style="' in output


def test_multiple_context_fields(manager):
    # add a new template with two placeholders
    manager.templates["multi.md"] = "User: {user}, ID: {id}"
    output = manager.render_template("multi", user="Bob", id=42)
    assert "User: Bob, ID: 42" in output


def test_markdown_special_characters(manager):
    # template that includes markdown list
    manager.templates["list.md"] = "- One\n- Two\n- Three"
    html = manager.render_template("list")
    # markdown2 transforms list into <ul> and inlined <li> tags
    assert "<ul" in html
    # Each list item should appear with inline style and content
    assert "<li style" in html and "One</li>" in html
    assert "<li style" in html and "Two</li>" in html
    assert "<li style" in html and "Three" in html


def test_footer_and_header_order(manager):
    # custom templates to verify order
    manager.templates["header.md"] = "[H]"
    manager.templates["footer.md"] = "[F]"
    manager.templates["body.md"] = "[B]"
    out = manager.render_template("body")
    # Should see header before body before footer
    seq = out.replace('\n','')
    assert "[H]" in seq and "[B]" in seq and "[F]" in seq
    assert seq.index("[H]") < seq.index("[B]") < seq.index("[F]")
