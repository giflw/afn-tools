package org.opengroove.jzbot.commands;

import java.net.URL;
import java.util.HashMap;

import org.jdom.Document;
import org.jdom.input.SAXBuilder;
import org.opengroove.jzbot.Command;
import org.opengroove.jzbot.JZBot;
import org.opengroove.jzbot.ResponseException;
import org.opengroove.jzbot.storage.Factoid;

public class WeatherCommand implements Command
{
    // yahoo: http://weather.yahooapis.com/forecastrss?p=94089
    // weatherbug: A7686974884
    
    public String getName()
    {
        return "weather";
    }
    
    public void run(String channel, boolean pm, String sender, String hostname,
        String arguments)
    {
        if (arguments.equals(""))
            throw new ResponseException(
                "You need to specify a zip code. For example, ~weather 12345");
        Factoid weatherFactoid = null;
        if (channel != null)
            weatherFactoid =
                JZBot.storage.getChannel(channel).getFactoid("weathertemplate");
        if (weatherFactoid == null)
            weatherFactoid = JZBot.storage.getFactoid("weathertemplate");
        if (weatherFactoid == null)
            throw new ResponseException("The weathertemplate factoid does not exist.");
        HashMap<String, String> map = new HashMap<String, String>();
        try
        {
            URL url =
                new URL(
                    "http://a7686974884.isapi.wxbug.net/WxDataISAPI/WxDataISAPI.dll?Magic=10991&RegNum=0&ZipCode="
                        + arguments.replace("&", "")
                        + "&Units=0&Version=7&Fore=0&t=123456");
            Object content = url.openConnection().getContent();
            throw new ResponseException("Type is " + content.getClass().getName());
        }
        catch (Exception e)
        {
            String result =
                JZBot.runFactoid(weatherFactoid, channel, sender, new String[0], map);
            e.printStackTrace();
            throw new RuntimeException(e.getClass().getName() + ": " + e.getMessage(),
                e);
        }
    }
}
