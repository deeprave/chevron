# Diagnostics and logging

Chevron is quiet by default. Recoverable Mustache behaviour such as a missing partial renders an empty result without writing to the process log. Enable diagnostics only when an application wants them.

```python
import logging
import chevron

logger = logging.getLogger("myapp.templates")
html = chevron.render(
    "{{> optional_banner}}<main>{{content}}</main>",
    {"content": "Ready"},
    logger=logger,
    log_level=logging.DEBUG,
)
```

Pass a standard-library `logging.Logger` or `logging.LoggerAdapter` through `logger`. Chevron does not add handlers, change levels, or alter propagation; those remain application policy. A supplied logger takes precedence over `warn`.

`warn=True` enables Chevron's historical default warning diagnostics. `log_level=logging.INFO` includes render lifecycle messages. `logging.DEBUG` adds bounded value-resolution and partial-selection decisions. Dynamic-partial diagnostics intentionally avoid recording the resolved selector value or template data.

Logging is synchronous in both APIs. Use the standard logging package's queue-based handlers if a destination could block; Chevron does not require a special async logger or wrapper.
