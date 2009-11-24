package jw.jzbot.fact.functions.irc;

import jw.jzbot.JZBot;
import jw.jzbot.fact.ArgumentList;
import jw.jzbot.fact.FactContext;
import jw.jzbot.fact.FactoidException;
import jw.jzbot.fact.Function;
import jw.jzbot.fact.Sink;

import org.jibble.pircbot.User;

public class IsvoicedFunction extends Function
{
    
    @Override
    public void evaluate(Sink sink, ArgumentList arguments, FactContext context)
    {
        String channel;
        String user;
        if (arguments.length() == 1)
        {
            channel = context.getChannel();
            user = arguments.get(0);
        }
        else
        {
            channel = arguments.get(0);
            user = arguments.get(1);
        }
        User[] users = JZBot.bot.getUsers(channel);
        for (User userObject : users)
        {
            System.out.println("Scanning for user " + userObject.getNick());
            if (userObject.getNick().equalsIgnoreCase(user))
            {
                if (userObject.hasVoice())
                    return "1";
                else
                    return "0";
            }
        }
        throw new FactoidException("Isvoiced on user \"" + user + "\", channel \""
                + channel + "\": user is not connected, consider using {{ifjoined}} "
                + "to see if the user is joined");
    }
    
    public String getName()
    {
        return "isop";
    }
    
    @Override
    public String getHelp(String topic)
    {
        return "Syntax: {{isvoiced||<channel>||<nick>}} -- Exactly the same as {{isop}}, "
                + "but checks to see if the user is voiced. On most servers, "
                + "this is mode +v.";
    }
    
}
