from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Token,
)

_BG = "#080c10" # background
_FG = "#b5bdc5" # foreground
_COMMENT = "#878d96" # comments, docstrings
_CONSTANT = "#5080ff" # numbers and Nones
_FIELD = "#7ac098" # classes 
_KEYWORD = "#a665d0" # def, class, if, else, for, while, …
_LITERAL = "#ca7050"   # preprocessor / decorators
_METHOD = "#c8b670"    # functions
_NAMESPACE = "#a3a0d8" # namespaces
_OPERATOR = "#ff7279" # imports
_PARAMETER = "#50b0e0" # function parameters, tags
_STRING = "#e0a076"   # string literals, dates
_TYPE = "#0ab6ba" #types  of variables
_VARIABLE = "#9ac6e0" # jeje almost all of the texts
_ERROR = "#fa4d56"   # errors, tracebacks, deleted diff lines
_SUCCESS = "#42be65" # inserted diff lines
_TITLE = "#5579f0"   # headings


class MidnightStyle(Style):

    background_color = _BG
    default_color = _FG
    highlight_color = "#012749"  # visual selection color

    styles = {
        Token:                      _FG,
        Error:                      _ERROR,

        # ── Comments ──────────────────────────────────────────────────────
        Comment:                    f"italic {_COMMENT}",
        Comment.Hashbang:           f"italic {_COMMENT}",
        Comment.Multiline:          f"italic {_COMMENT}",
        Comment.Single:             f"italic {_COMMENT}",
        Comment.Special:            f"italic {_COMMENT}",
        Comment.Preproc:            _LITERAL,
        Comment.PreprocFile:        _STRING,

        # ── Keywords ──────────────────────────────────────────────────────
        Keyword:                    _KEYWORD,
        Keyword.Constant:           _CONSTANT,
        Keyword.Declaration:        _KEYWORD,
        Keyword.Namespace:          _OPERATOR,   # import / use
        Keyword.Pseudo:             _KEYWORD,
        Keyword.Reserved:           _KEYWORD,
        Keyword.Type:               _TYPE,

        # ── Names ─────────────────────────────────────────────────────────
        Name:                       _VARIABLE,
        Name.Attribute:             _FIELD,
        Name.Builtin:               _KEYWORD,
        Name.Builtin.Pseudo:        _KEYWORD,    # self, cls, None, True, False
        Name.Class:                 _TYPE,
        Name.Constant:              _CONSTANT,
        Name.Decorator:             _LITERAL,
        Name.Entity:                _FIELD,
        Name.Exception:             _TYPE,
        Name.Function:              _METHOD,
        Name.Function.Magic:        _METHOD,
        Name.Label:                 _OPERATOR,
        Name.Namespace:             _NAMESPACE,
        Name.Other:                 _VARIABLE,
        Name.Property:              _FIELD,
        Name.Tag:                   _PARAMETER,
        Name.Variable:              _PARAMETER,
        Name.Variable.Class:        _VARIABLE,
        Name.Variable.Global:       _VARIABLE,
        Name.Variable.Instance:     _FIELD,
        Name.Variable.Magic:        _PARAMETER,

        # ── Literals ──────────────────────────────────────────────────────
        Literal:                    _STRING,
        Literal.Date:               _STRING,

        # ── Strings ───────────────────────────────────────────────────────
        String:                     _STRING,
        String.Affix:               _STRING,
        String.Backtick:            _STRING,
        String.Char:                _STRING,
        String.Delimiter:           _STRING,
        String.Doc:                 f"italic {_COMMENT}",
        String.Double:              _STRING,
        String.Escape:              _OPERATOR,
        String.Heredoc:             _STRING,
        String.Interpol:            _OPERATOR,
        String.Other:               _STRING,
        String.Regex:               _LITERAL,
        String.Single:              _STRING,
        String.Symbol:              _STRING,

        # ── Numbers ───────────────────────────────────────────────────────
        Number:                     _CONSTANT,
        Number.Bin:                 _CONSTANT,
        Number.Float:               _CONSTANT,
        Number.Hex:                 _CONSTANT,
        Number.Integer:             _CONSTANT,
        Number.Integer.Long:        _CONSTANT,
        Number.Oct:                 _CONSTANT,

        # ── Operators ─────────────────────────────────────────────────────
        Operator:                   _OPERATOR,
        Operator.Word:              _KEYWORD,    # and, or, not, in, is

        # ── Punctuation ───────────────────────────────────────────────────
        Punctuation:                _FG,
        Punctuation.Marker:         _OPERATOR,

        # ── Generic (diffs, prompts, …) ───────────────────────────────────
        Generic:                    _FG,
        Generic.Deleted:            _ERROR,
        Generic.Emph:               "italic",
        Generic.Error:              _ERROR,
        Generic.Heading:            f"bold {_TITLE}",
        Generic.Inserted:           _SUCCESS,
        Generic.Output:             _COMMENT,
        Generic.Prompt:             _KEYWORD,
        Generic.Strong:             "bold",
        Generic.Subheading:         f"bold {_NAMESPACE}",
        Generic.Traceback:          _ERROR,
        Generic.Underline:          "underline",
    }
