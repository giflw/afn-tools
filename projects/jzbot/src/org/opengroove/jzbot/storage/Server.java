package org.opengroove.jzbot.storage;

import net.sf.opengroove.common.proxystorage.ListType;
import net.sf.opengroove.common.proxystorage.Property;
import net.sf.opengroove.common.proxystorage.ProxyBean;
import net.sf.opengroove.common.proxystorage.StoredList;

@ProxyBean
public interface Server
{
    @Property
    public String getUrl();
    
    public void setUrl(String url);
    
    @Property
    @ListType(Operator.class)
    public StoredList<Operator> getOperators();
    
    @Property
    @ListType(Room.class)
    public StoredList<Room> getRooms();
}
