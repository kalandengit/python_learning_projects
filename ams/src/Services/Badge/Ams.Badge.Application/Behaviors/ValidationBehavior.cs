using FluentValidation;
using MediatR;

namespace Ams.Badge.Application.Behaviors;

/// <summary>
/// MediatR pipeline behavior (ADR-002): every command passes its
/// FluentValidation validators before the handler runs. Failures surface as
/// <see cref="ValidationException"/> and map to RFC 7807 422 in the API layer.
/// </summary>
public sealed class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (validators.Any())
        {
            var context = new ValidationContext<TRequest>(request);
            var results = await Task.WhenAll(
                validators.Select(v => v.ValidateAsync(context, cancellationToken)));
            var failures = results.SelectMany(r => r.Errors).Where(f => f is not null).ToList();
            if (failures.Count > 0)
                throw new ValidationException(failures);
        }

        return await next();
    }
}

// VERIFY: RequestHandlerDelegate takes no args in MediatR 12.4.x; newer majors add a CancellationToken overload.
