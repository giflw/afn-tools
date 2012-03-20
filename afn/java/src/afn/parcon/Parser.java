package afn.parcon;

public abstract class Parser {
    public abstract Result parse(String text, int position, int end,
            Parser space);
    
    public Object parseString(String text) {
        return null;
    }
    
    public int consume(String text, int position, int end) {
        Result result = parse(text, position, end, Invalid.invalid);
        while (result.matched) {
            position = result.end;
            result = parse(text, position, end, Invalid.invalid);
        }
        return position;
    }
    
    public Then then(Parser next) {
        return new Then(this, next);
    }
}
