package jw.jircs;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Queue;
import java.util.concurrent.LinkedBlockingQueue;

/**
 * Jircs: Java IRC Server. This is a simplistic IRC server. It's not designed
 * for production environments; I mainly wrote it to allow me to test out an IRC
 * bot I'm writing (http://jzbot.googlecode.com) when I'm not connected to the
 * internet. Every other dang IRC server takes a minute or so to try and look up
 * my hostname before realizing that I'm not even connected to the internet.
 * Jircs specifically doesn't do that.
 * 
 * @author Alexander Boyd
 * 
 */
public class Connection implements Runnable
{
    public static class Channel
    {
        private ArrayList<Connection> channelMembers = new ArrayList<Connection>();
        private String topic;
        protected String name;
        
        public void send(String toSend)
        {
            synchronized (mutex)
            {
                for (Connection con : channelMembers)
                {
                    con.send(toSend);
                }
            }
        }
        
        public void memberQuit(String nick)
        {
            
        }
    }
    
    public static final Object mutex = new Object();
    private Socket socket;
    private String username;
    private String hostname;
    private String nick;
    private String description;
    public static Map<String, Connection> connectionMap = new HashMap<String, Connection>();
    public static Map<String, Channel> channelMap = new HashMap<String, Channel>();
    private static String globalServerName;
    
    public Connection(Socket socket)
    {
        this.socket = socket;
    }
    
    public String getRepresentation()
    {
        return nick + "!" + username + "@" + hostname;
    }
    
    /**
     * @param args
     */
    public static void main(String[] args) throws Throwable
    {
        if (args.length == 0)
        {
            System.out.println("Usage: java jw.jircs.Connection <servername>");
        }
        globalServerName = args[0];
        ServerSocket ss = new ServerSocket(6898);
        while (true)
        {
            Socket s = ss.accept();
            Connection jircs = new Connection(s);
            Thread thread = new Thread(jircs);
            thread.start();
        }
    }
    
    public enum Command
    {
        NICK(1, 1)
        {
            @Override
            public void run(Connection con, String prefix, String[] arguments)
                    throws Exception
            {
                if (con.nick == null)
                    doFirstTimeNick(con, arguments[0]);
                else
                    doSelfSwitchNick(con, arguments[0]);
            }
            
            private void doSelfSwitchNick(Connection con, String nick)
            {
                synchronized (mutex)
                {
                    String oldNick = con.nick;
                    con.nick = filterAllowedNick(nick);
                    /*
                     * Now we need to notify all channels that we are on
                     */
                    for (Channel c : channelMap.values())
                    {
                        if (c.channelMembers.contains(this))
                            c.send(":" + oldNick + "!" + con.username + "@"
                                    + con.hostname + " NICK :" + con.nick);
                    }
                }
            }
            
            private void doFirstTimeNick(Connection con, String nick)
                    throws InterruptedException
            {
                con.nick = filterAllowedNick(nick);
                if (con.username == null)
                {
                    con.send("NOTICE AUTH :You must send USER before you "
                            + "send NICK. You will be disconnected.");
                    Thread.sleep(1000);
                    throw new RuntimeException();
                }
                /*
                 * Now we send the user a welcome message and everything.
                 */
            }
            
        },
        USER(1, 4)
        {
            @Override
            public void run(Connection con, String prefix, String[] arguments)
                    throws Exception
            {
                if (con.username != null)
                {
                    con.send("NOTICE AUTH :You can't change your user "
                            + "information after you've logged in right now.");
                    return;
                }
                con.username = arguments[0];
                String forDescription = arguments.length > 3 ? arguments[3]
                        : "(no description)";
                con.description = forDescription;
                /*
                 * Now we'll send the user their initial information.
                 */
                con.sendGlobal("001 " + con.nick + " :Welcome to "
                        + globalServerName + ", a Jircs-powered IRC network.");
                con.sendGlobal("375 " + con.nick + " :- " + globalServerName
                        + " Message of the Day -");
                con.sendGlobal("372 " + con.nick + " :- Hello. Welcome to "
                        + globalServerName + ", a Jircs-powered IRC network.");
                con
                        .sendGlobal("372 "
                                + con.nick
                                + " :- See http://code.google.com/p/jwutils/wiki/Jircs "
                                + "for more info on Jircs.");
                con.sendGlobal("376 " + con.nick + " :End of /MOTD command.");
            }
        },
        PING(1, 1)
        {
            @Override
            public void run(Connection con, String prefix, String[] arguments)
                    throws Exception
            {
                con.send(":" + globalServerName + " PONG " + globalServerName
                        + " :" + arguments[0]);
            }
        },
        JOIN(1, 2)
        {
            
            @Override
            public void run(Connection con, String prefix, String[] arguments)
                    throws Exception
            {
                if (arguments.length == 2)
                {
                    con.sendSelfNotice("This server does not support "
                            + "channel keys at "
                            + "this time. JOIN will act as if you "
                            + "hadn't specified any keys.");
                }
                String[] channelNames = arguments[0].split(",");
                for (String channelName : channelNames)
                {
                    if (!channelName.startsWith("#"))
                    {
                        con.sendSelfNotice("This server only allows "
                                + "channel names that "
                                + "start with a # sign.");
                        return;
                    }
                    if (channelName.contains(" "))
                    {
                        con.sendSelfNotice("This server does not allow spaces "
                                + "in channel names.");
                        return;
                    }
                }
                for (String channelName : channelNames)
                {
                    doJoin(con, channelName);
                }
            }
            
            public void doJoin(Connection con, String channelName)
            {
                if (!channelName.startsWith("#"))
                {
                    con
                            .sendSelfNotice("This server only allows channel names that "
                                    + "start with a # sign.");
                    return;
                }
                if (channelName.contains(" "))
                {
                    con
                            .sendSelfNotice("This server does not allow spaces in channel names.");
                }
                synchronized (mutex)
                {
                    Channel channel = channelMap.get(channelName);
                    if (channel == null)
                    {
                        channel = new Channel();
                        channel.name = channelName;
                        channelMap.put(channelName, channel);
                    }
                    if (channel.channelMembers.contains(con))
                    {
                        con.sendSelfNotice("You're already a member of "
                                + channelName);
                        return;
                    }
                    channel.channelMembers.add(con);
                    if (channel.topic != null)
                        con
                                .sendGlobal("332 " + con.nick + " :"
                                        + channel.topic);
                    else
                        con.sendGlobal("331 " + con.nick + " :No topic is set");
                }
            }
        };
        private int minArgumentCount;
        private int maxArgumentCount;
        
        private Command(int min, int max)
        {
            minArgumentCount = min;
            maxArgumentCount = max;
        }
        
        public int getMin()
        {
            return minArgumentCount;
        }
        
        public int getMax()
        {
            return maxArgumentCount;
        }
        
        public abstract void run(Connection con, String prefix,
                String[] arguments) throws Exception;
    }
    
    @Override
    public void run()
    {
        try
        {
            doServer();
        }
        catch (Exception e)
        {
            try
            {
                socket.close();
            }
            catch (Exception e2)
            {
            }
            e.printStackTrace();
        }
        finally
        {
            if (nick != null && connectionMap.get(nick) == this)
            {
                doNickRemoved();
            }
        }
    }
    
    protected void sendGlobal(String string)
    {
        send(":" + globalServerName + " " + string);
    }
    
    private void doNickRemoved()
    {
        synchronized (mutex)
        {
            connectionMap.remove(nick);
            for (Channel c : new ArrayList<Channel>(channelMap.values()))
            {
                if (c.channelMembers.contains(nick))
                    c.memberQuit(nick);
            }
        }
    }
    
    private LinkedBlockingQueue<String> outQueue = new LinkedBlockingQueue<String>(
            1000);
    
    private Thread outThread = new Thread()
    {
        public void run()
        {
            try
            {
                OutputStream out = socket.getOutputStream();
                while (true)
                {
                    String s = outQueue.take();
                    s = s.replace("\n", "").replace("\r", "");
                    s = s + "\r\n";
                    out.write(s.getBytes());
                    out.flush();
                }
            }
            catch (Exception e)
            {
                System.out.println("Outqueue died");
                outQueue.clear();
                outQueue = null;
                e.printStackTrace();
                try
                {
                    socket.close();
                }
                catch (Exception e2)
                {
                    e2.printStackTrace();
                }
            }
        }
    };
    
    private void doServer() throws Exception
    {
        hostname = socket.getRemoteSocketAddress().toString();
        System.out.println("Connection from host " + hostname);
        outThread.start();
        InputStream socketIn = socket.getInputStream();
        BufferedReader reader = new BufferedReader(new InputStreamReader(
                socketIn));
        String line;
        while ((line = reader.readLine()) != null)
        {
            processLine(line);
        }
        
    }
    
    private void processLine(String line) throws Exception
    {
        String prefix = "";
        if (line.startsWith(":"))
        {
            String[] tokens = line.split(" ", 2);
            prefix = tokens[0];
            line = (tokens.length > 1 ? tokens[1] : "");
        }
        String[] tokens1 = line.split(" ", 2);
        String command = tokens1[0];
        line = tokens1.length > 1 ? tokens1[1] : "";
        String[] tokens2 = line.split("(^| )\\:", 2);
        String trailing = null;
        line = tokens2[0];
        if (tokens2.length > 1)
            trailing = tokens2[1];
        ArrayList<String> argumentList = new ArrayList<String>();
        argumentList.addAll(Arrays.asList(line.split(" ")));
        if (trailing != null)
            argumentList.add(trailing);
        String[] arguments = argumentList.toArray(new String[0]);
        /*
         * Now we actually process the command.
         */
        if (command.matches("[0-9][0-9][0-9]"))
            command = "n" + command;
        Command commandObject = Command.valueOf(command.toLowerCase());
        if (commandObject == null)
            commandObject = Command.valueOf(command.toUpperCase());
        if (commandObject == null)
        {
            sendSelfNotice("That command (" + command
                    + ") isnt a supported command at this server.");
            return;
        }
        if (arguments.length < commandObject.getMin()
                || arguments.length > commandObject.getMax())
        {
            sendSelfNotice("Invalid number of arguments for this"
                    + " command, expected not more than "
                    + commandObject.getMax() + " and not less than "
                    + commandObject.getMin() + " but got " + arguments.length
                    + " arguments");
            return;
        }
        commandObject.run(this, prefix, arguments);
    }
    
    /**
     * Sends a notice from the server to the user represented by this
     * connection.
     * 
     * @param string
     *            The text to send as a notice
     */
    private void sendSelfNotice(String string)
    {
        send(":" + globalServerName + " NOTICE " + nick + " :" + string);
    }
    
    public static String filterAllowedNick(String theNick)
    {
        return theNick.replace(":", "").replace(" ", "").replace("!", "")
                .replace("@", "").replace("#", "");
    }
    
    private String[] padSplit(String line, String regex, int max)
    {
        String[] split = line.split(regex);
        String[] output = new String[max];
        for (int i = 0; i < output.length; i++)
        {
            output[i] = "";
        }
        for (int i = 0; i < split.length; i++)
        {
            output[i] = split[i];
        }
        return output;
    }
    
    public void send(String s)
    {
        Queue<String> testQueue = outQueue;
        if (testQueue != null)
            testQueue.add(s);
    }
}
