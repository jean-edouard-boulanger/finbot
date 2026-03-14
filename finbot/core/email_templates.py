import html

from finbot import model


def get_error_message(entry: model.LinkedAccountSnapshotEntry) -> str:
    if not entry.failure_details:
        return "Unknown error"
    errors = entry.failure_details
    if isinstance(errors, list):
        messages = [err.get("user_message", "Unknown error") for err in errors if isinstance(err, dict)]
        return "; ".join(messages) if messages else "Unknown error"
    return "Unknown error"


def render_snapshot_errors_html(
    error_entries: list[model.LinkedAccountSnapshotEntry],
) -> str:
    account_rows = ""
    for entry in error_entries:
        account_name = html.escape(entry.linked_account.account_name)
        error_message = html.escape(get_error_message(entry))
        dot_colour = html.escape(entry.linked_account.account_colour)
        account_rows += f"""\
<tr>
<td style="padding: 12px 16px; border-bottom: 1px solid #212536;">
<table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>
<td style="width: 12px; vertical-align: top; padding-top: 3px;">
<div style="width: 10px; height: 10px; border-radius: 50%; background-color: {dot_colour};"></div>
</td>
<td style="padding-left: 10px;">
<div style="font-size: 14px; font-weight: 600; color: #EFEDE9;">{account_name}</div>
<div style="font-size: 13px; color: #E84C4C; margin-top: 4px;">{error_message}</div>
</td>
</tr></table>
</td>
</tr>
"""

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #0B0E14;\
 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #0B0E14;">
<tr><td align="center" style="padding: 40px 20px;">
<table cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px;">
<!-- Header -->
<tr><td style="padding-bottom: 24px;">
<span style="font-size: 22px; font-weight: 700; color: #E8B517;">Finbot</span>
</td></tr>
<!-- Card -->
<tr><td style="background-color: #121722; border: 1px solid #212536; border-radius: 8px; overflow: hidden;">
<table cellpadding="0" cellspacing="0" border="0" width="100%">
<!-- Card header -->
<tr><td style="padding: 20px 16px 12px 16px;">
<div style="font-size: 17px; font-weight: 600; color: #EFEDE9;">Snapshot errors detected</div>
<div style="font-size: 13px; color: #6E7389; margin-top: 4px;">
{len(error_entries)} linked account(s) failed during the latest snapshot
</div>
</td></tr>
<!-- Account rows -->
{account_rows}\
</table>
</td></tr>
<!-- Footer -->
<tr><td style="padding-top: 24px; text-align: center;">
<span style="font-size: 12px; color: #6E7389;">This is an automated notification from Finbot.</span>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
