"""Task limits and explicitly uncertain proxy comparisons."""
import math

PROXY_LIMIT_HINT = ' (if this is a limit stated in the task text, record it under hard_limits with source_quote)'

def finite(value):
    return type(value) in (int, float) and math.isfinite(value)

def comparison_policy(comparison):
    errors, pending, warnings = [], [], []
    for limit in comparison.get('hard_limits', []):
        if not str(limit.get('source_quote') or '').strip() or not isinstance(limit.get('evidence'), dict):
            errors.append('hard limit requires task source_quote and evidence')
            continue
        direction=limit.get('direction'); value=limit.get('candidate_value'); bound=limit.get('limit')
        if direction not in ('HIGHER_IS_BETTER','LOWER_IS_BETTER') or not finite(bound) or not limit.get('metric'):
            errors.append('invalid hard limit')
        elif not finite(value): warnings.append('UNVERIFIED hard limit: '+limit['metric'])
        elif value < bound if direction=='HIGHER_IS_BETTER' else value > bound:
            errors.append('task hard limit violated: '+limit['metric'])
    proxies=list(comparison.get('proxy_metrics', []))
    for gate in comparison.get('gates', []):
        proxies.append(gate)
        warnings.append('legacy gate treated as proxy: '+str(gate.get('metric')))
    for proxy in proxies:
        a,b=proxy.get('baseline_value'),proxy.get('candidate_value')
        direction=proxy.get('direction')
        if not finite(a) or not finite(b) or direction not in ('HIGHER_IS_BETTER','LOWER_IS_BETTER'):
            warnings.append('UNVERIFIED proxy metric: '+str(proxy.get('metric')))
        elif b < a if direction=='HIGHER_IS_BETTER' else b > a:
            warnings.append('proxy metric is worse than baseline: '+str(proxy.get('metric'))+PROXY_LIMIT_HINT)
    primary=dict(comparison)
    if isinstance(comparison.get('primary'),dict): primary.update(comparison['primary'])
    a,b=primary.get('baseline_value'),primary.get('candidate_value')
    if finite(a) and finite(b) and primary.get('direction') in ('HIGHER_IS_BETTER','LOWER_IS_BETTER'):
        if b < a if primary['direction']=='HIGHER_IS_BETTER' else b > a:
            if str(primary.get('task_metric_ref') or '').strip():
                errors.append('candidate scores lower on the task metric under identical evaluation')
            else: warnings.append('primary proxy metric is worse than baseline: '+str(primary.get('metric'))+PROXY_LIMIT_HINT)
    if comparison.get('selection')=='CURRENT_BASELINE':
        option=comparison.get('best_alternative')
        if not isinstance(option,dict) or not option.get('name') or not isinstance(option.get('metric_values'),dict) or not option.get('rejection_reason') or option.get('rejection_basis') not in ('HARD_LIMIT','TASK_METRIC','SAFETY','OTHER'):
            pending.append('CURRENT_BASELINE requires best_alternative with rejection_basis')
        else:
            ref=option.get('evidence')
            if not isinstance(ref,dict) or any(not isinstance(ref.get(k),str) or not ref[k].strip() for k in ('path','sha256')):
                pending.append('best_alternative evidence missing')
            names=set(option['metric_values'])
            proxy_names={p.get('metric') for p in proxies}
            if option['rejection_basis']=='OTHER' or names and names<=proxy_names:
                warnings.append('NO_OP: baseline retained by a criterion not in the task')
    return {'errors':errors,'pending':pending,'warnings':warnings}
