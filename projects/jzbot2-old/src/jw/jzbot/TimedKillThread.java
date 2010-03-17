package jw.jzbot;

public class TimedKillThread extends Thread
{
    public volatile boolean active = true;
    private Thread target;
    
    public static final int MAX_FACT_RUN_TIME = 1000 * 60;
    
    public volatile int maxRunTime = MAX_FACT_RUN_TIME;
    
    public TimedKillThread(Thread target)
    {
        this.target = target;
        setDaemon(true);
    }
    
    @SuppressWarnings("deprecation")
    public void run()
    {
        try
        {
            for (int i = 0; i < (maxRunTime / 5000); i++)
            {
                Thread.sleep(5000);
                if (!active)
                    return;
            }
        }
        catch (InterruptedException e)
        {
            e.printStackTrace();
        }
        if (active)
            target
                    .stop(new FactTimeExceededError(
                            "This factoid or command took too long to run. Factoids and "
                                + "commands can only run for " + (maxRunTime / 1000)
                                + " seconds."));
    }
}
