import { ConflictError, NotFoundError } from '@asa/errors';
import { ToolRegistry } from './tool';
import { calculatorTool } from './testing/fixtures';

describe('ToolRegistry', () => {
  it('registers and resolves tools', () => {
    const registry = new ToolRegistry([calculatorTool]);
    expect(registry.has('add')).toBe(true);
    expect(registry.get('add').description).toBe('Adds two numbers.');
  });

  it('rejects duplicate tool names', () => {
    const registry = new ToolRegistry([calculatorTool]);
    expect(() => registry.register(calculatorTool)).toThrow(ConflictError);
  });

  it('throws NotFoundError for unknown tools', () => {
    expect(() => new ToolRegistry().get('missing')).toThrow(NotFoundError);
  });

  it('builds model tool definitions for the named tools', () => {
    const registry = new ToolRegistry([calculatorTool]);
    const defs = registry.toDefinitions(['add']);
    expect(defs).toEqual([
      {
        name: 'add',
        description: 'Adds two numbers.',
        parameters: calculatorTool.parameters,
      },
    ]);
  });
});
