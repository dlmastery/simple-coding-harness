# Additional scope fixture

Input A: majority overall accuracy 0.871473. Input B: linear balanced accuracy 0.744955. The metrics differ. A scoped memory check returns needs-clarification. Removing that scope check and taking the larger number would choose majority, whose balanced accuracy is only 0.5. This numerical comparison is invalid; it is not a new task result.
