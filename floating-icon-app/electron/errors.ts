/**
 * Safely extract a message from a caught value.
 *
 * `catch` bindings are `unknown` under `strict`, and a thrown value is not
 * guaranteed to be an Error, so narrow before reaching for `.message`.
 */
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}
