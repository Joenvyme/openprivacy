import argparse
import json
import sys
import time
from typing import Sequence

from ._cli.common import CliHelpFormatter, add_checkpoint_arg, resolve_prog
from ._cli.args import (
    add_common_redaction_args,
    iter_inputs,
    using_interactive_prompt,
)

_SUBCOMMANDS = frozenset({"redact", "eval", "train", "anonymize", "deanonymize"})
_ROOT_DESCRIPTION = (
    "OpenAI Privacy Filter (OPF): redact text to remove PII. "
    "Redact locally via CLI and interactive mode; run evaluations; "
    "or fine-tune on your own labeled dataset.\n\n"
    "Subcommands:\n"
    "  redact       Redact text locally (default, implied).\n"
    "  anonymize    Anonymize text with reversible mapping.\n"
    "  deanonymize  Restore original text from anonymized text.\n"
    "  eval         Run encoder eval on a ground-truth dataset.\n"
    "  train        Fine-tune a checkpoint on a local labeled dataset.\n"
    "Default mode: redact\n"
    "  The redact mode has additional flags; see `opf redact --help`."
)
_REDACT_DESCRIPTION = "Redact text to remove PII."
_ANONYMIZE_DESCRIPTION = "Anonymize text with reversible mapping."
_DEANONYMIZE_DESCRIPTION = "Restore original text from anonymized text."


def build_parser(*, prog: str | None = None) -> argparse.ArgumentParser:
    """Build the top-level ``opf`` parser."""
    parser = argparse.ArgumentParser(
        description=_ROOT_DESCRIPTION,
        formatter_class=CliHelpFormatter,
        prog=prog or resolve_prog("opf"),
    )
    return parser


def build_redaction_parser(*, prog: str | None = None) -> argparse.ArgumentParser:
    """Build the parser for the redaction CLI mode."""
    parser = argparse.ArgumentParser(
        description=_REDACT_DESCRIPTION,
        formatter_class=CliHelpFormatter,
        prog=prog or resolve_prog("opf"),
    )
    input_group = parser.add_argument_group("Input / Source")
    runtime_group = parser.add_argument_group("Model / Runtime")
    decode_group = parser.add_argument_group("Decode")
    output_group = parser.add_argument_group("Output")
    input_group.add_argument(
        "positional_text",
        nargs="?",
        help="Text input to filter.",
    )
    add_checkpoint_arg(runtime_group)
    add_common_redaction_args(
        parser,
        runtime_group=runtime_group,
        decode_group=decode_group,
        output_group=output_group,
    )
    output_group.add_argument(
        "--format",
        choices=("text", "json"),
        default=None,
        help="Print redacted text or the structured JSON schema output.",
    )
    input_group.add_argument(
        "-f",
        "--text-file",
        action="append",
        default=None,
        help=(
            "Text file path; each file is treated as one full input example "
            "(repeat for multiple files)."
        ),
    )
    parser.set_defaults(
        interactive_banner="OPF redaction. Type '/exit' (or 'quit') to stop.",
        interactive_prompt="text> ",
    )
    return parser


def parse_args(
    argv: Sequence[str] | None = None, *, prog: str | None = None
) -> argparse.Namespace:
    """Parse redaction-mode arguments and normalize positional text."""
    args = build_redaction_parser(prog=prog).parse_args(argv)
    if args.positional_text:
        text_items = [] if args.text is None else list(args.text)
        args.text = [args.positional_text, *text_items]
    return args


def _run_redaction_command(argv: Sequence[str], *, prog: str | None = None) -> None:
    """Run the redaction CLI mode."""
    args = parse_args(argv, prog=prog)
    if args.json_indent < 0:
        raise ValueError("json_indent must be >= 0")

    from ._api import RedactionResult
    from ._common.terminal_colors import build_label_color_map
    from ._cli.render import (
        build_redactor_from_args,
        build_session_runtime_view,
        print_session_header,
        render_color_coded_text,
        render_color_legend,
        run_summary_line,
    )

    interactive_mode = using_interactive_prompt(args)
    effective_format = args.format or ("json" if interactive_mode else "text")
    redactor = build_redactor_from_args(
        args,
        output_text_only=effective_format == "text",
    )
    runtime = None
    label_colors = None
    if effective_format == "json":
        runtime = build_session_runtime_view(redactor)
        if interactive_mode:
            print_session_header(
                checkpoint=runtime.checkpoint,
                device=runtime.device,
                encoding_name=runtime.active_encoding_name,
                n_ctx=runtime.n_ctx,
                output_mode=runtime.output_mode,
            )
        if runtime.output_mode != "redacted":
            legend_labels = runtime.label_info.span_class_names
            label_colors = build_label_color_map(legend_labels)
    for text in iter_inputs(args):
        infer_start = time.perf_counter()
        result = redactor.redact(text)
        latency_ms = (time.perf_counter() - infer_start) * 1000.0
        if effective_format == "text":
            print(str(result))
            continue
        if not isinstance(result, RedactionResult):
            raise TypeError("json output requires a structured RedactionResult")
        print(
            run_summary_line(
                summary=result.summary,
                latency_ms=latency_ms,
            ),
            file=sys.stderr,
        )
        print(json.dumps(result.to_dict(), indent=args.json_indent, ensure_ascii=False))
        if args.print_color_coded_text and label_colors is not None:
            color_coded_text = render_color_coded_text(
                text=result.text,
                spans=result.detected_spans,
                label_colors=label_colors,
            )
            print(render_color_legend(label_colors=label_colors))
            print("color coded text:")
            print(color_coded_text if color_coded_text else "(empty)")


def _run_eval_command(argv: Sequence[str]) -> None:
    """Dispatch to the eval CLI implementation."""
    if any(arg in {"-h", "--help"} for arg in argv):
        from ._eval.args import parse_args as parse_eval_args

        parse_eval_args(argv, prog=f"{resolve_prog('opf')} eval")
        return
    from ._eval.runner import main as eval_main

    eval_main(argv, prog=f"{resolve_prog('opf')} eval")


def _run_train_command(argv: Sequence[str]) -> None:
    """Dispatch to the train CLI implementation."""
    if any(arg in {"-h", "--help"} for arg in argv):
        from ._train.args import parse_args as parse_train_args

        parse_train_args(list(argv), prog=f"{resolve_prog('opf')} train")
        return
    from ._train.runner import main as train_main

    train_main(argv, prog=f"{resolve_prog('opf')} train")


def _run_anonymize_command(argv: Sequence[str], *, prog: str | None = None) -> None:
    """Run the anonymization CLI mode."""
    parser = argparse.ArgumentParser(
        description=_ANONYMIZE_DESCRIPTION,
        formatter_class=CliHelpFormatter,
        prog=prog or resolve_prog("opf anonymize"),
    )
    input_group = parser.add_argument_group("Input / Source")
    runtime_group = parser.add_argument_group("Model / Runtime")
    decode_group = parser.add_argument_group("Decode")
    output_group = parser.add_argument_group("Output")
    
    input_group.add_argument(
        "positional_text",
        nargs="?",
        help="Text input to anonymize.",
    )
    add_checkpoint_arg(runtime_group)
    add_common_redaction_args(
        parser,
        runtime_group=runtime_group,
        decode_group=decode_group,
        output_group=output_group,
    )
    output_group.add_argument(
        "--map-output",
        type=str,
        required=True,
        help="Output path for the anonymization map JSON file.",
    )
    input_group.add_argument(
        "-f",
        "--text-file",
        action="append",
        default=None,
        help=(
            "Text file path; each file is treated as one full input example "
            "(repeat for multiple files)."
        ),
    )
    
    args = parser.parse_args(argv)
    if args.positional_text:
        text_items = [] if args.text is None else list(args.text)
        args.text = [args.positional_text, *text_items]
    
    from ._cli.render import build_redactor_from_args
    from pathlib import Path
    
    redactor = build_redactor_from_args(args, output_text_only=False)
    
    for text in iter_inputs(args):
        anonymized_text, anon_map = redactor.anonymize(text)
        
        # Save the map
        map_path = Path(args.map_output)
        anon_map.save(map_path)
        
        # Print anonymized text
        print(anonymized_text)
        print(f"\nAnonymization map saved to: {map_path}", file=sys.stderr)
        print(f"Map ID: {anon_map.map_id}", file=sys.stderr)


def _run_deanonymize_command(argv: Sequence[str], *, prog: str | None = None) -> None:
    """Run the deanonymization CLI mode."""
    parser = argparse.ArgumentParser(
        description=_DEANONYMIZE_DESCRIPTION,
        formatter_class=CliHelpFormatter,
        prog=prog or resolve_prog("opf deanonymize"),
    )
    
    parser.add_argument(
        "anonymized_text",
        nargs="?",
        help="Anonymized text to restore (or use --text-file).",
    )
    parser.add_argument(
        "--map-file",
        type=str,
        required=True,
        help="Path to the anonymization map JSON file.",
    )
    parser.add_argument(
        "-f",
        "--text-file",
        type=str,
        help="File containing anonymized text.",
    )
    
    args = parser.parse_args(argv)
    
    from ._core.anonymization_map import AnonymizationMap
    from pathlib import Path
    
    # Load the mapping
    map_path = Path(args.map_file)
    if not map_path.exists():
        print(f"Error: Map file not found: {map_path}", file=sys.stderr)
        raise SystemExit(1)
    
    anon_map = AnonymizationMap.load(map_path)
    
    # Get the anonymized text
    if args.text_file:
        anonymized_text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.anonymized_text:
        anonymized_text = args.anonymized_text
    elif not sys.stdin.isatty():
        anonymized_text = sys.stdin.read()
    else:
        print("Error: No input text provided", file=sys.stderr)
        parser.print_help()
        raise SystemExit(1)
    
    # Deanonymize
    from ._api import deanonymize
    
    original_text = deanonymize(anonymized_text, anon_map)
    print(original_text)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the unified ``opf`` command-line entrypoint."""
    argv_list = list(argv or [])
    if argv is None:
        argv_list = sys.argv[1:]
    if argv_list and argv_list[0] in _SUBCOMMANDS:
        command = argv_list[0]
        subcommand_argv = argv_list[1:]
        if command == "redact":
            _run_redaction_command(
                subcommand_argv,
                prog=f"{resolve_prog('opf')} redact",
            )
            return
        if command == "anonymize":
            _run_anonymize_command(
                subcommand_argv,
                prog=f"{resolve_prog('opf')} anonymize",
            )
            return
        if command == "deanonymize":
            _run_deanonymize_command(
                subcommand_argv,
                prog=f"{resolve_prog('opf')} deanonymize",
            )
            return
        if command == "eval":
            _run_eval_command(subcommand_argv)
            return
        if command == "train":
            _run_train_command(subcommand_argv)
            return
    if any(arg in {"-h", "--help"} for arg in argv_list):
        build_parser().print_help()
        raise SystemExit(0)
    _run_redaction_command(argv_list)


if __name__ == "__main__":
    main()
