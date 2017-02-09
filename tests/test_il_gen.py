"""Tests for the AST->IL phase of the compiler."""

import unittest

import token_kinds
import il_commands
from errors import error_collector
from il_gen import ILCode
from il_gen import SymbolTable
from lexer import Lexer
from parser import Parser


class ILGenTests(unittest.TestCase):
    """Tests for the AST->IL phase of the compiler.

    We're lowkey cheating here--these are more of integration tests than unit
    tests, because we're also tokenizing/parsing the input string. However,
    writing out the parsed form for every test is a lot of struggle that's not
    really worth it given that we have good tests of the parsing phase
    anyway.

    """

    def setUp(self):
        """Clear the error collector before each new test."""
        error_collector.clear()

    def test_return_literal(self):
        """Test returning a single literal."""
        source = "int main() { return 15; }"
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Return(15))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_return_sum(self):
        """Test returning the sum of two literals."""
        source = "int main() { return 10 + 20; }"
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Add("t1", 10, 20))
        expected_code.add(il_commands.Return("t1"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_return_variable(self):
        """Test returning a variable."""
        source = "int main() { int a; return a; }"
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Return("a"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_return_variable_sum(self):
        """Test returning the sum of two variables."""
        source = "int main() { int a; int b; return a+b; }"
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Add("t1", "a", "b"))
        expected_code.add(il_commands.Return("t1"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_return_variable_equal_sum(self):
        """Test returning a variable that the sum of two variables."""
        source = "int main() { int a; int b; int c; c = a + b; return c; }"
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Add("t1", "a", "b"))
        expected_code.add(il_commands.Set("c", "t1"))
        expected_code.add(il_commands.Return("c"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_return_variable_equal_product(self):
        """Test returning a variable that is the product of two variables."""
        source = "int main() { int a; int b; int c; c = a * b; return c; }"
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Mult("t1", "a", "b"))
        expected_code.add(il_commands.Set("c", "t1"))
        expected_code.add(il_commands.Return("c"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_equal_return_value(self):
        """Test that 'a = b' returns the value of 'a'."""
        source = """
                 int main() {
                     int a; int b; int c;
                     c = a = b;
                     return c;
                 }"""
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Set("a", "b"))
        expected_code.add(il_commands.Set("c", "a"))
        expected_code.add(il_commands.Return("c"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_complex_expression(self):
        """Test a single complex expression."""
        source = """
                 int main() {
                     int a; int b; int c;
                     c = (a * b) + (c + a) * a;
                    return c;
                 }"""
        il_code = self.make_il_code(source)

        expected_code = ILCode()
        expected_code.add(il_commands.Mult("t1", "a", "b"))
        expected_code.add(il_commands.Add("t2", "c", "a"))
        expected_code.add(il_commands.Mult("t3", "t2", "a"))
        expected_code.add(il_commands.Add("t4", "t1", "t3"))
        expected_code.add(il_commands.Set("c", "t4"))
        expected_code.add(il_commands.Return("c"))
        expected_code.add(il_commands.Return(0))

        self.assertEqual(il_code, expected_code)

    def test_error_unassignable(self):
        """Verify errors when expression on left of '=' is unassignable."""
        source = """
                 int main() {
                     3 = 4;
                 }"""
        self.make_il_code(source)

        descrip = "error: expression on left of '=' is not assignable"
        self.assertEqual(len(error_collector.issues), 1)
        self.assertTrue(descrip in str(error_collector.issues[0]))

    def make_il_code(self, source):
        """Make IL code from the given source.

        returns (ILCode) - the produced IL code object

        """
        lexer = Lexer(token_kinds.symbol_kinds, token_kinds.keyword_kinds)
        token_list = lexer.tokenize([(source, "test.c", "7")])

        ast_root = Parser(token_list).parse()

        il_code = ILCode()
        symbol_table = SymbolTable()
        ast_root.make_code(il_code, symbol_table)
        return il_code


if __name__ == "__main__":
    unittest.main()
