from crapper.languages.ruby import functions_in_source


def test_decision_points_in_a_method():
    source = """
class Grader
  def grade(x, y)
    return 1 if x && y
    return 2 unless x
    n = x ? 1 : 2
    n += 1 while n < 3
    n -= 1 until n < 1
    x&.zero?
    a = x || y
    b = x and y
    if x
      1
    elsif y
      2
    else
      3
    end
    for i in [1] do i end
    case x
    when 1 then 1
    when 2, 3 then 2
    else 0
    end
    case y
    in 1 then 1
    in 2 then 2
    end
    begin
      n
    rescue ArgumentError
      0
    rescue KeyError
      1
    end
  end
end
"""
    [fn] = functions_in_source(source, "app/models/grader.rb", "/proj")
    # 1 + if/unless/?:/while/until (5) + &. + || + and + && (4) + if/elsif (2)
    # + for + 2 when + 2 in + 2 rescue
    assert (fn.namespace, fn.name, fn.complexity) == ("Grader", "grade", 19)


def test_namespaces_and_singleton_methods():
    source = """
module Billing
  class Plan < Base
    def price; 1; end
    def self.build; end
    class << self
      def parse(x)
        x ? 1 : 2
      end
    end
    class Tier
      def rank; end
    end
  end
end

class Billing::Invoice
  def total; end
end

class Shop::Cart::Line
  def self.zero; end
end

def helper; end
"""
    functions = functions_in_source(source, "app/models/plan.rb", "/proj")
    assert [(fn.namespace, fn.name, fn.complexity) for fn in functions] == [
        ("Billing::Plan", "price", 1),
        ("Billing::Plan", "self.build", 1),
        ("Billing::Plan", "self.parse", 2),
        ("Billing::Plan::Tier", "rank", 1),
        ("Billing::Invoice", "total", 1),
        ("Shop::Cart::Line", "self.zero", 1),
        ("Object", "helper", 1),
    ]


def test_nested_def_and_blocks_stay_in_the_enclosing_method():
    source = """
class A
  def outer(items)
    items.each do |i|
      next if i
    end
    inner = ->(n) { n ? 1 : 2 }
    def helper; end
  end
end
"""
    functions = functions_in_source(source, "a.rb", "/proj")
    assert [(fn.name, fn.complexity) for fn in functions] == [("outer", 3)]
    assert (functions[0].start_line, functions[0].end_line) == (3, 9)
