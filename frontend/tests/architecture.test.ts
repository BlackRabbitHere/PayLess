import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import ts from 'typescript'

const root = join(dirname(fileURLToPath(import.meta.url)), '../src')
function files(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry =>
    entry.isDirectory() ? files(join(directory, entry.name)) : /\.tsx?$/.test(entry.name) ? [join(directory, entry.name)] : [])
}

test('views cannot call HTTP transports or import business implementations', () => {
  const views = files(root).filter(path => /[/\\](view|components)[/\\]/.test(path))
  assert.ok(views.length > 10)
  for (const path of views) {
    const source = ts.createSourceFile(path, readFileSync(path, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
    function visit(node: ts.Node) {
      if (ts.isCallExpression(node)) {
        assert.doesNotMatch(node.expression.getText(source), /^(fetch|axios(?:\.|$)|optimize|recommendedRoutes|understandQuery)/,
          `Transport or business calculation in view: ${path}`)
      }
      if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
        const clause = node.importClause
        const typeOnly = clause?.isTypeOnly || (clause?.namedBindings && ts.isNamedImports(clause.namedBindings)
          && clause.namedBindings.elements.every(element => element.isTypeOnly))
        if (!typeOnly) assert.doesNotMatch(node.moduleSpecifier.text, /(?:\/api\/|demoOptimizer|queryUnderstanding|axios)/, path)
      }
      ts.forEachChild(node, visit)
    }
    visit(source)
  }
})

test('model modules stay independent from React, controllers and network transport', () => {
  for (const path of files(root).filter(path => /[/\\]model[/\\]/.test(path))) {
    const text = readFileSync(path, 'utf8')
    assert.doesNotMatch(text, /from ['"](?:react|react-router-dom|axios)['"]/, path)
    assert.doesNotMatch(text, /from ['"][^'"]*\/(?:controller|view|api)\//, path)
    assert.doesNotMatch(text, /\bfetch\s*\(/, path)
  }
})
