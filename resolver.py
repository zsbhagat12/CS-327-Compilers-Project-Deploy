from dataclasses_sim import *


def resolve(program: AST, environment: Environment = None) -> AST:
    if environment is None:
        environment = Environment()
    environment.program = program
    def resolve_(program: AST) -> AST:
        return resolve(program, environment)
    
    match program:
        case NumLiteral(_) as N:
            return N
        case BoolLiteral(_) as B:
            return B
        case StringLiteral(_) as SL:
            return SL
        case BinOp("=" as aop, MutVar(name) as m, right) :
            if not environment.check(name):
                environment.add(name, m)
            else:
                environment.update(name, m)
            # environment.enter_scope()
            m = resolve_(m)
            mutvar = environment.get(name)
            r = resolve_(right)
            mutvar.put(r)
            
            # environment.exit_scope()
            return BinOp(aop, m, r)
        case BinOp("+="as aop, MutVar(name)as m, right) | BinOp("-="as aop, MutVar(name)as m, right) | BinOp("/="as aop, MutVar(name)as m, right) | BinOp("*="as aop, MutVar(name)as m, right) | BinOp("**="as aop, MutVar(name)as m, right):
            if not environment.check(name):
                environment.add(name, m)
            # environment.enter_scope()
            m = resolve_(m)
            mutvar = environment.get(name)
            r = resolve_(right)
            mutvar.put(r)
            
            # environment.exit_scope()
            return BinOp(aop, m, r)
        case BinOp(o, left, right):
            return BinOp(o, resolve_(left), resolve_(right))
        case UnOp(o, mid):
            return UnOp(o, resolve_(mid))
        case Variable(name):
            return environment.get(name)
        case MutVar(name) as m :
            if not environment.check(name):
                environment.add(name, m)
            return environment.get(name)
        case Let(Variable(name) as v, e1, e2):
            re1 = resolve_(e1)
            environment.enter_scope()
            environment.add(name, v)
            re2 = resolve_(e2)
            environment.exit_scope()
            return Let(v, re1, re2)
        case Statement(command ,statement):
            return Statement(command, resolve_(statement))
                
                
       

        case IfElse(c, b, e):
            return IfElse(resolve_(c), resolve_(b), resolve_(e))
        case LetFun(Variable(name) as v, params, body, expr):
            environment.enter_scope()
            environment.add(name, v)
            environment.enter_scope()
            for param in params:
                environment.add(param.name, param)
            rbody = resolve_(body)
            environment.exit_scope()
            rexpr = resolve_(expr)
            environment.exit_scope()
            return LetFun(v, params, rbody, rexpr)
        case Function(MutVar(name) as m, params , body) | Function(Variable(name) as m, params , body):
            
            # environment.add(name, m)
            if not environment.check(name):
                environment.add(name, m)
            else:
                environment.update(name, m)
            mutvar = environment.get(name)
            
            environment.enter_scope()
            # rparams = []
            for param in params:
                environment.add(param.name, param)
        
                # rparams.append(resolve_(param))
            rbody = resolve_(body)
            environment.exit_scope()
            e = FnObject(params, rbody)
            mutvar.put(e)
            return Function(mutvar, params, rbody)
        case Seq(things):
            environment.enter_scope()
            v = []
            for thing in things:
                v.append(resolve_(thing))
                
            environment.exit_scope()
            return Seq(v)
        case FunCall(fn, args):
            rfn = resolve_(fn)
            rargs = []
            for arg in args:
                rargs.append(resolve_(arg))
            return FunCall(rfn, rargs)
        case FunCall(MutVar(name) as m, args):
            m = resolve_(m)
            fn = environment.get(name).get()
            argv = []
            
            for arg in args:
                argv.append(resolve_(arg))
            return FunCall(m, argv)
            
        case While(c, b):
            
            return While(resolve_(c), resolve_(b))
# def eval(program: AST, environment: Environment = None) -> Value:
#     if environment is None:
#         environment = Environment()

#     def eval_(program):
#         return eval(program, environment)

#     match program:
#         case NumLiteral(value):
#             return value
#         case Variable(_) as v:
#             return environment.get(v)
#         case Let(Variable(_) as v, e1, e2) | LetMut(Variable(_) as v, e1, e2):
#             v1 = eval_(e1)
#             environment.enter_scope()
#             environment.add(v, v1)
#             v2 = eval_(e2)
#             environment.exit_scope()
#             return v2
#         case BinOp("+", left, right):
#             return eval_(left) + eval_(right)
#         case BinOp("-", left, right):
#             return eval_(left) - eval_(right)
#         case BinOp("*", left, right):
#             return eval_(left) * eval_(right)
#         case BinOp("/", left, right):
#             return eval_(left) / eval_(right)
#         case Put(Variable(_) as v, e):
#             environment.update(v, eval_(e))
#             return environment.get(v)
#         case Get(Variable(_) as v):
#             return environment.get(v)
#         case Seq(things):
#             v = None
#             for thing in things:
#                 v = eval_(thing)
#             return v
#         case LetFun(Variable(_) as v, params, body, expr):
#             environment.enter_scope()
#             environment.add(v, FnObject(params, body))
#             v = eval_(expr)
#             environment.exit_scope()
#             return v
#         case FunCall(Variable(_) as v, args):
#             fn = environment.get(v)
#             argv = []
#             for arg in args:
#                 argv.append(eval_(arg))
#             environment.enter_scope()
#             for param, arg in zip(fn.params, argv):
#                 environment.add(param, arg)
#             v = eval_(fn.body)
#             environment.exit_scope()
#             return v
#     raise InvalidProgram()

def test_resolve():
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    e = Let(Variable.make("a"), NumLiteral(0), Variable.make("a"))
    # pp.pprint(e)
    re = resolve(e)
    # pp.pprint(re)

    e = LetFun(Variable.make("foo"), [Variable.make("a")], FunCall(Variable.make("foo"), [Variable.make("a")]),
               Let(Variable.make("g"), Variable.make("foo"),
                   LetFun(Variable.make("foo"), [Variable.make("a")], NumLiteral(0),
                          FunCall(Variable.make("g"), [NumLiteral(0)]))))
    pp.pprint(e)
    pp.pprint(r := resolve(e))
    print(eval(r))

# test_resolve()