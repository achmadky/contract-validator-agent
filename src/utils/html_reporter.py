import os
import json
import datetime
from typing import Dict, Any, List, Optional, Union

class HTMLReporter:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, contract_name: str, validation_results: Dict[str, Any], 
                        performance_data: Dict[str, Any],
                        lsr_sample: Optional[Union[Dict[str, Any], List[Any]]] = None,
                        current_sample: Optional[Union[Dict[str, Any], List[Any]]] = None) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"{os.path.splitext(contract_name)[0]}_{timestamp}.html"
        report_path = os.path.join(self.output_dir, report_filename)

        status = validation_results.get("status", "UNKNOWN")
        reason = validation_results.get("reason", "No reason provided")
        status_color = self._get_status_color(status)

        html_content = f"""
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"UTF-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
            <title>Contract Validation Report: {contract_name}</title>
            <style>
                :root {{
                    --border: #e5e7eb;
                    --bg-soft: #f8f9fb;
                    --bg-card: #ffffff;
                    --text-muted: #5f6368;
                    --pass: #2e7d32;
                    --pass-bg: #dff2e1; /* slightly brighter but soft */
                    --warn: #b26a00;
                    --warn-bg: #ffefdb; /* slightly brighter but soft */
                    --fail: #c62828;
                    --fail-bg: #fee6e6; /* slightly brighter but soft */
                    --unknown: #6b7280;
                    --unknown-bg: #f0f2f5;
                }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 980px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: var(--bg-soft); padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--border); }}
                .status-badge {{ display: inline-block; padding: 6px 12px; border-radius: 14px; font-weight: 600; color: white; background-color: {status_color}; font-size: 12px; }}
                .section {{ margin-bottom: 18px; border: 1px solid var(--border); border-radius: 8px; padding: 14px; background: white; }}
                .section-title {{ margin: 0 0 10px 0; font-size: 16px; }}
                .sub-title {{ margin: 8px 0 6px; font-size: 14px; color: var(--text-muted); }}
                .diff-item {{ margin: 10px 0; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background-color: var(--bg-soft); }}
                .diff-removed {{ border-color: #f8d7da; background-color: #fff5f6; }}
                .diff-added {{ border-color: #d4edda; background-color: #f6fff6; }}
                .diff-changed {{ border-color: #ffeeba; background-color: #fffdf2; }}
                .performance {{ display: flex; align-items: center; gap: 10px; }}
                .performance-indicator {{ width: 10px; height: 10px; border-radius: 50%; }}
                .code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace; background-color: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
                pre.code-block {{ background: #f5f5f5; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 8px 0; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }}
                th {{ background-color: var(--bg-soft); }}
                details {{ margin: 8px 0; }}
                summary {{ cursor: pointer; font-weight: 600; font-size: 13px; }}
                .hint {{ font-size: 12px; color: var(--text-muted); margin-top: 6px; }}
                .list {{ margin: 0; padding-left: 18px; }}
                /* JSON syntax highlighting */
                .json-block {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace; background-color: #f5f5f5; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 8px 0; white-space: pre; }}
                .json-box {{ border: 1px solid #e0e0e0; border-radius: 4px; padding: 4px; margin: 2px 0; background-color: #fafafa; }}
                .json-line {{ display: block; }}
                .json-line {{ padding: 2px 6px; margin: 1px 0; border-radius: 4px; }}
                .json-key {{ color: #0451a5; }}
                .json-string {{ color: #a31515; }}
                .json-number {{ color: #098658; }}
                .json-boolean {{ color: #0000ff; }}
                .json-null {{ color: #0000ff; }}
                .json-punctuation {{ color: #000000; }}
                .line-removed {{ background-color: var(--fail-bg); color: var(--fail); }}
                .line-added {{ background-color: var(--pass-bg); color: var(--pass); }}
                .line-changed {{ background-color: var(--warn-bg); color: var(--warn); }}
                /* Response boxes and layout */
                .side-by-side {{ display: flex; gap: 20px; align-items: flex-start; }}
                .response-box {{ flex: 1; border: 1px solid var(--border); border-radius: 8px; padding: 10px; background-color: var(--bg-soft); }}
                .box-title {{ margin: 0 0 6px; font-weight: 600; font-size: 13px; color: #333; }}
                /* Toggle controls removed */
            </style>
        </head>
        <body>
            <div class=\"header\">
                <h1 style=\"margin:0 0 6px\">Contract Validation Report</h1>
                <p style=\"margin:0\"><strong>Contract:</strong> {contract_name}</p>
                <p style=\"margin:0 0 6px;color:var(--text-muted)\"><strong>Generated:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <div class=\"status-badge\">{status}</div>
            </div>

            {self._generate_deterministic_section(validation_results, lsr_sample, current_sample)}
            {self._generate_performance_section(performance_data)}

            <div class=\"section\">
                <h2 class=\"section-title\">Summary</h2>
                <p style=\"margin:6px 0\"><strong>Final Status:</strong> {status}</p>
                <p style=\"margin:6px 0\"><strong>Reason:</strong> {reason}</p>
                {self._generate_action_recommendation(validation_results)}
            </div>
        </body>
        </html>
        """

        with open(report_path, "w") as f:
            f.write(html_content)
        return report_path

    def generate_aggregate_report(self, items: List[Dict[str, Any]]) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"contracts_aggregate_{timestamp}.html"
        report_path = os.path.join(self.output_dir, report_filename)

        # Compute overview stats
        total = len(items)
        status_counts = {"PASS": 0, "PASS_WITH_WARNING": 0, "FAIL": 0, "UNKNOWN": 0}
        breaking_count = 0
        changes_count = 0
        anomaly_count = 0
        latencies: List[float] = []
        for item in items:
            validation = item.get("validation_results", {})
            status = validation.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            if validation.get("critical_diff"):
                breaking_count += 1
            changes = validation.get("all_other_changes") or validation.get("all_changes")
            if changes:
                changes_count += 1
            perf = item.get("performance_data", {})
            if perf.get("is_anomaly"):
                anomaly_count += 1
            if "current_latency" in perf:
                try:
                    latencies.append(float(perf["current_latency"]))
                except Exception:
                    pass
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        pass_count = status_counts.get('PASS', 0)
        warn_count = status_counts.get('PASS_WITH_WARNING', 0)
        fail_count = status_counts.get('FAIL', 0)
        unknown_count = status_counts.get('UNKNOWN', 0)
        def pct(val: int) -> float:
            return (val / total * 100.0) if total else 0.0
        overview_block = f"""
        <div class=\"section\">
            <h2 class=\"section-title\">Overview</h2>
            <div class=\"overview\">
                <div class=\"dist-bar\">
                    <div class=\"seg-pass\" style=\"width:{pct(pass_count):.2f}%\"></div>
                    <div class=\"seg-warn\" style=\"width:{pct(warn_count):.2f}%\"></div>
                    <div class=\"seg-fail\" style=\"width:{pct(fail_count):.2f}%\"></div>
                    <div class=\"seg-unknown\" style=\"width:{pct(unknown_count):.2f}%\"></div>
                </div>
                <div class=\"legend\"> 
                    <span><span class=\"dot pass\"></span>Pass: {pass_count}</span>
                    <span><span class=\"dot warn\"></span>Warnings: {warn_count}</span>
                    <span><span class=\"dot fail\"></span>Fail: {fail_count}</span>
                    <span><span class=\"dot unknown\"></span>Unknown: {unknown_count}</span>
                </div>
                <p class=\"sub-title\" style=\"margin:4px 0 0\">Total: {total} • Failures: {fail_count} • Breaking: {breaking_count} • Perf anomalies: {anomaly_count}</p>
            </div>
            <p class=\"hint\">Glance at distribution above; prioritize Failures and Breaking first.</p>
        </div>
        """

        header = f"""
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"UTF-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
            <title>Contracts Aggregate Report</title>
            <style>
                :root {{
                    --border: #eee;
                    --bg-soft: #fafafa;
                    --text-muted: #666;
                    --bg-card: #ffffff;
                    --pass: #2e7d32;
                    --pass-bg: #dff2e1;
                    --warn: #b26a00;
                    --warn-bg: #ffefdb;
                    --fail: #c62828;
                    --fail-bg: #fee6e6;
                    --unknown: #6b7280;
                    --unknown-bg: #f0f2f5;
                }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 980px; margin: 0 auto; padding: 20px; }}
                .section {{ margin-bottom: 18px; border: 1px solid var(--border); border-radius: 12px; padding: 16px; background: var(--bg-card); box-shadow: 0 1px 2px rgba(0,0,0,0.03); }}
                .section-title {{ margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 8px; font-size: 16px; }}
                .sub-title {{ margin: 8px 0 6px; font-size: 14px; color: var(--text-muted); }}

                /* Overview visuals */
                .overview {{ display: grid; grid-template-columns: 1fr; gap: 12px; }}
                .dist-bar {{ display: flex; height: 14px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); background: var(--bg-soft); }}
                .seg-pass {{ background: #d8f3dc; }}
                .seg-warn {{ background: #ffe8c2; }}
                .seg-fail {{ background: #f8d7da; }}
                .seg-unknown {{ background: #e5e7eb; }}
                .legend {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-size: 12px; color: var(--text-muted); }}
                .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }}
                .dot.pass {{ background: var(--pass); }}
                .dot.warn {{ background: var(--warn); }}
                .dot.fail {{ background: var(--fail); }}
                .dot.unknown {{ background: var(--unknown); }}
                .status-badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; margin-left:6px; font-weight:600; }}
                .contract-header {{ display: flex; align-items: center; padding: 10px; border-radius: 8px; margin-bottom: 1px; background: var(--bg-soft); transition: background-color 0.2s; }}
                .contract-header:hover {{ background: #f0f2f5; }}
                .contract-name {{ font-weight: 600; font-size: 14px; margin-right: auto; }}
                .contract-detail {{ margin-bottom: 8px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
                .contract-detail summary {{ padding: 0; }}
                .contract-detail summary::-webkit-details-marker {{ display: none; }}
                .contract-icon {{ margin-right: 8px; color: var(--text-muted); }}

                /* Diff and content visuals */
                .diff-item {{ margin: 10px 0; padding: 10px; border-radius: 8px; border: 1px solid var(--border); background-color: var(--bg-soft); }}
                .diff-removed {{ border-color: #f1a7ad; background-color: #fee6e6; }}
                .diff-added {{ border-color: #a9dbb6; background-color: #e7f6ed; }}
                .diff-changed {{ border-color: #ffe3a3; background-color: #fff7e6; }}
                .performance {{ display: flex; align-items: center; gap: 10px; }}
                .performance-indicator {{ width: 10px; height: 10px; border-radius: 50%; }}
                .code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace; background-color: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
                pre.code-block {{ background: #f5f5f5; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 8px 0; }}
                details {{ margin: 8px 0; }}
                summary {{ cursor: pointer; font-weight: 600; font-size: 13px; }}
                .hint {{ font-size: 12px; color: var(--text-muted); margin-top: 6px; }}
                .list {{ margin: 0; padding-left: 18px; }}
            </style>
        </head>
        <body>
            <h1 style=\"margin:0 0 10px\">Contracts Aggregate Report</h1>
            <p style=\"margin:0 0 14px;color:var(--text-muted)\"><strong>Generated:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            {overview_block}
        """

        body_blocks: List[str] = []
        for item in items:
            name = item.get("contract_name", "unknown.json")
            validation = item.get("validation_results", {})
            perf = item.get("performance_data", {})
            lsr_sample = item.get("lsr_sample")
            current_sample = item.get("current_sample")
            status = validation.get("status", "UNKNOWN")
            status_style = self._get_status_style(status)

            block = f"""
            <details class=\"contract-detail\"> 
              <summary><span class=\"contract-name\">{name}</span> <span class=\"status-badge\" style=\"{status_style}\">{status.replace('_',' ')}</span></summary>
              {self._generate_deterministic_section(validation, lsr_sample, current_sample)}
              {self._generate_performance_section(perf)}
              <div class=\"section\">
                <h2 class=\"section-title\">Summary</h2>
                <p style=\"margin:6px 0\"><strong>Final Status:</strong> {status}</p>
                <p style=\"margin:6px 0\"><strong>Reason:</strong> {validation.get('reason','')}</p>
                {self._generate_action_recommendation(validation)}
              </div>
            </details>
            """
            body_blocks.append(block)

        footer = """
        </body>
        </html>
        """

        with open(report_path, "w") as f:
            f.write(header + "".join(body_blocks) + footer)
        return report_path

    def _get_status_color(self, status: str) -> str:
        # Softer, pastel backgrounds using CSS variables
        status_colors = {
            "PASS": "var(--pass-bg)",
            "PASS_WITH_WARNING": "var(--warn-bg)",
            "FAIL": "var(--fail-bg)",
            "UNKNOWN": "var(--unknown-bg)",
        }
        return status_colors.get(status, "var(--unknown-bg)")

    def _get_status_style(self, status: str) -> str:
        styles = {
            "PASS": "background-color: var(--pass-bg); color: var(--pass); border: 1px solid rgba(46,125,50,0.35);",
            "PASS_WITH_WARNING": "background-color: var(--warn-bg); color: var(--warn); border: 1px solid rgba(178,106,0,0.4);",
            "FAIL": "background-color: var(--fail-bg); color: var(--fail); border: 1px solid rgba(198,40,40,0.4);",
            "UNKNOWN": "background-color: var(--unknown-bg); color: var(--unknown); border: 1px solid rgba(107,114,128,0.35);",
        }
        return styles.get(status, styles["UNKNOWN"]) 

    def _generate_deterministic_section(self, validation_results: Dict[str, Any],
                                        lsr_sample: Optional[Union[Dict[str, Any], List[Any]]] = None,
                                        current_sample: Optional[Union[Dict[str, Any], List[Any]]] = None) -> str:
        critical_diff = validation_results.get("critical_diff", {})
        all_changes = validation_results.get("all_other_changes", {}) or validation_results.get("all_changes", {})

        html = '<div class="section">'
        html += '<h2 class="section-title">Deterministic Validation</h2>'

        # If no differences found, show a simple message
        if not critical_diff and not all_changes:
            html += '<p style="margin:6px 0">No differences detected. Contract is fully compatible.</p>'
            html += '</div>'
            return html

        # Show only the Unified Diff view
        if lsr_sample is not None or current_sample is not None:
            html += '<h3 style="margin:12px 0 6px">Unified Diff</h3>'
            html += self._generate_unified_diff_view(lsr_sample, current_sample)
        
        # Add explanation section
        html += '<h3 style="margin:12px 0 6px">Explanation of Changes</h3>'
        
        # Breaking changes
        if critical_diff:
            html += '<div class="diff-item diff-removed">'
            html += '<h4 style="margin:0 0 6px">Breaking Changes</h4>'
            html += '<ul class="list">'
            
            # Missing keys
            if "MISSING_KEYS" in critical_diff:
                for item in critical_diff["MISSING_KEYS"]:
                    html += f'<li><code class="code">{item}</code></li>'
            
            # Type changes
            if "TYPE_CHANGES" in critical_diff:
                for path, change in critical_diff["TYPE_CHANGES"].items():
                    old_type = change.get("old_type", "unknown")
                    new_type = change.get("new_type", "unknown")
                    html += f'<li><code class="code">{path}</code>: Type changed from {old_type} to {new_type}</li>'
            
            html += '</ul>'
            html += '</div>'
        
        # Other changes
        if all_changes:
            # Added keys
            if "dictionary_item_added" in all_changes:
                html += '<div class="diff-item diff-added">'
                html += '<h4 style="margin:0 0 6px">New Parameters</h4>'
                html += '<ul class="list">'
                for item in all_changes["dictionary_item_added"]:
                    html += f'<li><code class="code">{item}</code></li>'
                html += '</ul>'
                html += '</div>'
            
            # Value changes
            if "values_changed" in all_changes:
                html += '<div class="diff-item diff-changed">'
                html += '<h4 style="margin:0 0 6px">Value Changes</h4>'
                html += '<ul class="list">'
                for path, change in all_changes["values_changed"].items():
                    old_value = change.get("old_value", "")
                    new_value = change.get("new_value", "")
                    html += f'<li><code class="code">{path}</code>: Changed from {old_value} to {new_value}</li>'
                html += '</ul>'
                html += '</div>'
        
        html += '</div>'
        return html
            
    def _format_json_as_single_lines(self, html, json_obj, special_keys1, special_keys2, special_keys3, side):
        """Format JSON with each parameter on a single line"""
        if isinstance(json_obj, dict):
            html += '<div class="json-box">\n'
            
            # Process each key-value pair
            items = list(json_obj.items())
            for i, (key, value) in enumerate(items):
                # Determine if this key is special
                line_class = ""
                if side == "lsr":
                    # For LSR side, highlight missing keys and changed values
                    for path in special_keys1:  # missing_keys
                        if path.endswith(key) or path == key:
                            line_class = "line-removed"
                            break
                    if not line_class:
                        for path in special_keys2:  # type_changes
                            if path.endswith(key) or path == key:
                                line_class = "line-changed"
                                break
                    if not line_class:
                        for path in special_keys3:  # value_changes
                            if path.endswith(key) or path == key:
                                line_class = "line-changed"
                                break
                else:  # current
                    # For current side, highlight added keys and changed values
                    for path in special_keys1:  # added_keys
                        if path.endswith(key) or path == key:
                            line_class = "line-added"
                            break
                    if not line_class:
                        for path in special_keys2:  # type_changes
                            if path.endswith(key) or path == key:
                                line_class = "line-changed"
                                break
                    if not line_class:
                        for path in special_keys3:  # value_changes
                            if path.endswith(key) or path == key:
                                line_class = "line-changed"
                                break
                
                # Format the value as a string
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = json.dumps(value, ensure_ascii=False)
                
                # Create the line with proper comma
                line = f'  "{key}": {value_str}{", " if i < len(items) - 1 else ""}'
                
                # Apply syntax highlighting and line highlighting
                html += self._format_json_with_syntax_highlighting(line, line_class) + '\n'
            
            html += '</div>\n'
        elif isinstance(json_obj, list):
            html += '<div class="json-box">\n'
            
            # Process each item in the list
            for i, item in enumerate(json_obj):
                if isinstance(item, (dict, list)):
                    value_str = json.dumps(item, ensure_ascii=False)
                else:
                    value_str = json.dumps(item, ensure_ascii=False)
                
                # Create the line with proper comma
                line = f'  {value_str}{", " if i < len(json_obj) - 1 else ""}'
                
                # Apply syntax highlighting
                html += self._format_json_with_syntax_highlighting(line) + '\n'
            
            html += '</div>\n'
        else:
            # For primitive values
            html += '<div class="json-box">' + json.dumps(json_obj, ensure_ascii=False) + '</div>\n'
        
        return html

    def _flatten_json(self, obj: Any, prefix: str = "") -> Dict[str, str]:
        """Flatten a JSON-like object into path -> serialized value mappings.
        Paths follow DeepDiff-style (e.g., root['a']['b'][0])."""
        import json as _json
        flat: Dict[str, str] = {}

        def _walk(value: Any, path: str):
            if isinstance(value, dict):
                for k, v in value.items():
                    _walk(v, f"{path}['{k}']")
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    _walk(v, f"{path}[{i}]")
            else:
                try:
                    flat[path] = _json.dumps(value, ensure_ascii=False)
                except Exception:
                    flat[path] = str(value)

        base = prefix or "root"
        _walk(obj, base)
        return flat

    def _generate_unified_diff_view(self, lsr_sample: Optional[Union[Dict[str, Any], List[Any]]],
                                    current_sample: Optional[Union[Dict[str, Any], List[Any]]]) -> str:
        """Produce a git-like unified diff where each top-level parameter is one line.
        - Unchanged lines have no symbol (context).
        - Removed lines start with '-' and are red.
        - Added lines start with '+' and are green.
        - Changed lines show '-' and '+' pair in yellow.
        Fallback to flattened diff if inputs are not both dicts/lists.
        """
        import json as _json

        def _serialize(v: Any) -> str:
            try:
                return _json.dumps(v, ensure_ascii=False)
            except Exception:
                return str(v)

        def _is_empty(serialized: Optional[str]) -> bool:
            if serialized is None:
                return True
            s = serialized.strip()
            return s in ("\"\"", "null", "[]", "{}")

        html = '<div class="response-box"><div class="json-block">'

        # Dict vs Dict: compare top-level keys only
        if isinstance(lsr_sample, dict) or isinstance(current_sample, dict):
            l_dict = lsr_sample if isinstance(lsr_sample, dict) else {}
            c_dict = current_sample if isinstance(current_sample, dict) else {}
            all_keys = sorted(set(l_dict.keys()) | set(c_dict.keys()))
            for key in all_keys:
                l_has = key in l_dict
                c_has = key in c_dict
                l_val = _serialize(l_dict[key]) if l_has else None
                c_val = _serialize(c_dict[key]) if c_has else None
                if l_has and not c_has:
                    html += self._format_json_with_syntax_highlighting(f'- "{key}": {l_val}', "line-removed") + '\n'
                elif not l_has and c_has:
                    html += self._format_json_with_syntax_highlighting(f'+ "{key}": {c_val}', "line-added") + '\n'
                elif l_has and c_has and l_val != c_val:
                    # If new value becomes empty, treat as removal (red)
                    if _is_empty(c_val):
                        html += self._format_json_with_syntax_highlighting(f'- "{key}": {l_val}', "line-removed") + '\n'
                        html += self._format_json_with_syntax_highlighting(f'+ "{key}": {c_val}', "line-removed") + '\n'
                    else:
                        html += self._format_json_with_syntax_highlighting(f'- "{key}": {l_val}', "line-changed") + '\n'
                        html += self._format_json_with_syntax_highlighting(f'+ "{key}": {c_val}', "line-changed") + '\n'
                else:
                    html += self._format_json_with_syntax_highlighting(f'  "{key}": {l_val}') + '\n'
            html += '</div></div>'
            return html

        # List vs List: compare by index
        if isinstance(lsr_sample, list) or isinstance(current_sample, list):
            l_list = lsr_sample if isinstance(lsr_sample, list) else []
            c_list = current_sample if isinstance(current_sample, list) else []
            max_len = max(len(l_list), len(c_list))
            for i in range(max_len):
                l_has = i < len(l_list)
                c_has = i < len(c_list)
                l_val = _serialize(l_list[i]) if l_has else None
                c_val = _serialize(c_list[i]) if c_has else None
                label = f'[{i}]'
                if l_has and not c_has:
                    html += self._format_json_with_syntax_highlighting(f'- {label}: {l_val}', "line-removed") + '\n'
                elif not l_has and c_has:
                    html += self._format_json_with_syntax_highlighting(f'+ {label}: {c_val}', "line-added") + '\n'
                elif l_has and c_has and l_val != c_val:
                    if _is_empty(c_val):
                        html += self._format_json_with_syntax_highlighting(f'- {label}: {l_val}', "line-removed") + '\n'
                        html += self._format_json_with_syntax_highlighting(f'+ {label}: {c_val}', "line-removed") + '\n'
                    else:
                        html += self._format_json_with_syntax_highlighting(f'- {label}: {l_val}', "line-changed") + '\n'
                        html += self._format_json_with_syntax_highlighting(f'+ {label}: {c_val}', "line-changed") + '\n'
                else:
                    html += self._format_json_with_syntax_highlighting(f'  {label}: {l_val}') + '\n'
            html += '</div></div>'
            return html

        # Fallback: show singular value comparison
        l_val = _serialize(lsr_sample) if lsr_sample is not None else None
        c_val = _serialize(current_sample) if current_sample is not None else None
        if l_val is not None and c_val is None:
            html += self._format_json_with_syntax_highlighting(f'- {l_val}', "line-removed") + '\n'
        elif l_val is None and c_val is not None:
            html += self._format_json_with_syntax_highlighting(f'+ {c_val}', "line-added") + '\n'
        elif l_val is not None and c_val is not None and l_val != c_val:
            html += self._format_json_with_syntax_highlighting(f'- {l_val}', "line-changed") + '\n'
            html += self._format_json_with_syntax_highlighting(f'+ {c_val}', "line-changed") + '\n'
        else:
            html += self._format_json_with_syntax_highlighting(f'  {l_val}') + '\n'

        html += '</div></div>'
        return html
            
    def _generate_performance_section(self, performance_data: Dict[str, Any]) -> str:
        is_anomaly = performance_data.get("is_anomaly", False)
        current_latency = performance_data.get("current_latency", 0)
        min_range = performance_data.get("min_range", 0)
        max_range = performance_data.get("max_range", 0)
        performance_color = "#f44336" if is_anomaly else "#4caf50"

        html = '<div class="section">'
        html += '<h2 class="section-title">Performance Validation</h2>'
        html += '<div class="performance">'
        html += f'<div class="performance-indicator" style="background-color: {performance_color};"></div>'
        if is_anomaly:
            html += f'<p style="margin:0"><strong>Warning:</strong> Latency ({current_latency:.4f}s) exceeds normal range ({min_range:.4f}s - {max_range:.4f}s).</p>'
        else:
            html += f'<p style="margin:0"><strong>OK:</strong> Latency ({current_latency:.4f}s) is within expected range ({min_range:.4f}s - {max_range:.4f}s).</p>'
        html += '</div>'
        html += '</div>'
        return html

    def _generate_action_recommendation(self, validation_results: Dict[str, Any]) -> str:
        status = validation_results.get("status", "UNKNOWN")
        if status == "FAIL":
            return """
            <div class=\"diff-item diff-removed\">
                <h3 style=\"margin:0 0 6px\">Recommended Action</h3>
                <p style=\"margin:0\">Fix the API to maintain backward compatibility. The breaking changes must be addressed.</p>
            </div>
            """
        elif status == "PASS_WITH_WARNING":
            return """
            <div class=\"diff-item diff-changed\">
                <h3 style=\"margin:0 0 6px\">Recommended Action</h3>
                <p style=\"margin:0\">Consider updating the contract to reflect the new structure. Run the patch command to update.</p>
            </div>
            """
        else:
            return ""

    def _resolve_path_value(self, data: Union[Dict[str, Any], List[Any]], path: str) -> Any:
        tokens: List[Union[str, int]] = []
        import re
        pos = 0
        while pos < len(path):
            key_m = re.search(r"\['([^']+)'\]", path[pos:])
            idx_m = re.search(r"\[(\d+)\]", path[pos:])
            next_key_pos = key_m.start() + pos if key_m else None
            next_idx_pos = idx_m.start() + pos if idx_m else None
            if next_key_pos is not None and (next_idx_pos is None or next_key_pos < next_idx_pos):
                key = key_m.group(1)
                tokens.append(key)
                pos = key_m.end() + pos
            elif next_idx_pos is not None:
                idx = int(idx_m.group(1))
                tokens.append(idx)
                pos = idx_m.end() + pos
            else:
                break
        try:
            cur = data
            for t in tokens:
                if isinstance(t, int):
                    cur = cur[t]
                else:
                    cur = cur[t]
            return cur
        except Exception:
            return None

    def _format_snippet(self, path: str, old_val: Any, new_val: Any, highlight: str) -> str:
        key_name = self._last_key_from_path(path)
        def to_json(v):
            try:
                return json.dumps(v, ensure_ascii=False)
            except Exception:
                return str(v)
        if highlight == "missing":
            return f"<div class='diff-item diff-removed'><strong>Missing</strong> <code class='code'>{path}</code><pre class='code-block'>\"{key_name}\": {to_json(old_val)}</pre></div>"
        if highlight == "changed":
            return (
                f"<div class='diff-item diff-changed'><strong>Changed</strong> <code class='code'>{path}</code>"
                f"<pre class='code-block'>- \"{key_name}\": {to_json(old_val)}\n+ \"{key_name}\": {to_json(new_val)}</pre></div>"
            )
        if highlight == "added":
            return f"<div class='diff-item diff-added'><strong>Added</strong> <code class='code'>{path}</code><pre class='code-block'>\"{key_name}\": {to_json(new_val)}</pre></div>"
        return ""

    def _format_json_with_syntax_highlighting(self, json_line, line_class=""):
        import re
        # Apply syntax highlighting to JSON elements (non-anchored to match more cases)
        # Highlight keys
        json_line = re.sub(r'(\"(?:\\.|[^\"\\])*\")\s*:', r'<span class="json-key">\1</span>:', json_line)

        # Highlight string values
        json_line = re.sub(r':\s*(\"(?:\\.|[^\"\\])*\")', r': <span class="json-string">\1</span>', json_line)

        # Highlight numbers
        json_line = re.sub(r':\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', r': <span class="json-number">\1</span>', json_line)

        # Highlight booleans
        json_line = re.sub(r':\s*(true|false)', r': <span class="json-boolean">\1</span>', json_line)

        # Highlight null
        json_line = re.sub(r':\s*(null)', r': <span class="json-null">\1</span>', json_line)

        # Highlight punctuation
        json_line = re.sub(r'([{}\[\],])', r'<span class="json-punctuation">\1</span>', json_line)

        # Apply line highlighting if specified; always wrap each line to ensure line breaks
        bg_color = ""
        if line_class == "line-added":
            bg_color = "background-color: var(--pass-bg);"
        elif line_class == "line-removed":
            bg_color = "background-color: var(--fail-bg);"
        elif line_class == "line-changed":
            bg_color = "background-color: var(--warn-bg);"
            
        if line_class:
            return f'<div class="json-line {line_class}" style="{bg_color}">{json_line}</div>'
        return f'<div class="json-line">{json_line}</div>'
        
    def _last_key_from_path(self, path: str) -> str:
        import re
        m = re.findall(r"\['([^']+)'\]", path)
        if m:
            return m[-1]
        idx = re.findall(r"\[(\d+)\]", path)
        return idx[-1] if idx else path