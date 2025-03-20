import torch as th
from loguru import logger


def check_grad_and_clip_(
    model: th.nn.Module, 
    model_name: str = 'model',
    max_norm: float = None,
    verbose: bool = 1,
    set_none_to_zero: bool = False
):
    grad_norm = 0.0
    # https://discuss.pytorch.org/t/how-to-inspect-whethet-there-is-nan-or-inf-in-gradients-after-amp/154791
    grad = th.cat([
        p.grad.data.flatten()
        for name, p in model.named_parameters()
        if p.requires_grad and p.grad is not None
    ])
    allisfinite = th.isfinite(grad).all().item()
    
    if not allisfinite:
        if verbose >= 1:
            logger.warning(f'Inf grad found in {model_name}')
        return False, grad_norm
    
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        elif param.grad is None:
            if verbose >= 1:
                logger.warning(f'None grad: {model_name} -> {name}')
            if set_none_to_zero:
                param.grad = th.zeros_like(param, device=param.device)
        else:
            # Check for zero gradients
            if th.all(param.grad.data == 0):
                if verbose >= 2:
                    logger.warning(f'Zero grad: {model_name} -> {name}')
                
            grad_norm += param.grad.data.norm(2).item() ** 2
                
    if max_norm is not None:
        th.nn.utils.clip_grad_norm_(model.parameters(), max_norm)
                
    return True, grad_norm ** 0.5
            
            
def count_params(model: th.nn.Module):
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    return all_param, trainable_params
