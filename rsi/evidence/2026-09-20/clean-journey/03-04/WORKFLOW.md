# Repair cycle

Check → valid: stop. Check → invalid: repair if fewer than two repairs have been used, then check again. After two ineffective repairs, stop with failure. The return edge carries attempts and the last missing-field result.
