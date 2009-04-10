package tests;

import javax.swing.JFrame;

import org.opengroove.sixjet.common.ui.jetpattern.JetPatternEditor;
import org.opengroove.sixjet.common.ui.jetpattern.Mark;
import org.opengroove.sixjet.common.ui.jetpattern.Track;

public class Test03
{
    
    /**
     * @param args
     */
    public static void main(String[] args)
    {
        JFrame f = new JFrame();
        f.getContentPane().setLayout(null);
        JetPatternEditor e = new JetPatternEditor(true);
        Track track = new Track(e);
        f.getContentPane().add(track);
        track.setSize(890, Mark.MARK_HEIGHT);
        track.setLocation(10, 40);
        Mark mark = new Mark(e, track);
        track.add(mark);
        mark.setSize(65, Mark.MARK_HEIGHT);
        mark.setLocation(120, 0);
        Mark mark2 = new Mark(e, track);
        track.add(mark2);
        mark2.setLocation(240, 0);
        mark2.setSize(15, Mark.MARK_HEIGHT);
        f.setSize(1000, 300);
        f.show();
    }
}
