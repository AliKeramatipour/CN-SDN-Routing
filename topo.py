from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )

        s1 = self.addHost( 's1' )
        s2 = self.addHost( 's2' )
        s3 = self.addHost( 's3' )
        s4 = self.addHost( 's4' )
        s5 = self.addHost( 's5' )
        s6 = self.addHost( 's6' )
        s7 = self.addHost( 's7' )
        s8 = self.addHost( 's8' )
        s9 = self.addHost( 's9' )
        s10 = self.addHost( 's10' )
        s11 = self.addHost( 's11' )
        s12 = self.addHost( 's12' )


        sw1 = self.addSwitch( 'sw1' )
        sw2 = self.addSwitch( 'sw2' )
        sw3 = self.addSwitch( 'sw3' )
        sw4 = self.addSwitch( 'sw4' )
        sw5 = self.addSwitch( 'sw5' )
        sw6 = self.addSwitch( 'sw6' )
        sw7 = self.addSwitch( 'sw7' )
        sw8 = self.addSwitch( 'sw8' )
        sw9 = self.addSwitch( 'sw9' )
        sw10 = self.addSwitch( 'sw10' )
        sw11 = self.addSwitch( 'sw11' )
        sw12 = self.addSwitch( 'sw12' )
        sw13 = self.addSwitch( 'sw13' )
        sw14 = self.addSwitch( 'sw14' )
        sw15 = self.addSwitch( 'sw15' )
        sw16 = self.addSwitch( 'sw16' )

        # Add links
        self.addLink( h1, sw13 )
        self.addLink( h2, sw14 )
        self.addLink( h3, sw1 )

        self.addLink( sw13, sw3, bw=15, cls=TCLink )
        self.addLink( sw13, sw7, bw=15, cls=TCLink )

        self.addLink( sw14, sw7, bw=20, cls=TCLink )

        self.addLink( sw15, sw8 )

        self.addLink( sw16, sw8 , bw=15, cls=TCLink )
        self.addLink( sw16, sw12 , bw=10, cls=TCLink )

        self.addLink( sw3, sw2 , delay = 100, cls=TCLink)
        self.addLink( sw4, sw1 , delay = 100, cls=TCLink)
        self.addLink( sw4, sw2 , delay = 50, cls=TCLink)

        self.addLink( sw7, sw6 , delay = 100, cls=TCLink)
        self.addLink( sw8, sw5 , delay = 100, cls=TCLink)
        self.addLink( sw8, sw6 , delay = 50, cls=TCLink)

        self.addLink( sw11, sw9 , delay = 50, cls=TCLink)
        self.addLink( sw11, sw10 , delay= 100, cls=TCLink)
        self.addLink( sw12, sw10 , delay= 50, cls=TCLink)

        self.addLink( sw1, s1 )
        self.addLink( sw1, s2 )

        self.addLink( sw2, s3 )
        self.addLink( sw2, s4 )

        self.addLink( sw3, s5 )
        self.addLink( sw3, s6 )

        self.addLink( sw4, s7 )
        self.addLink( sw4, s8 )

        self.addLink( sw5, s9 )
        self.addLink( sw5, s10 )

        self.addLink( sw6, s11 )
        self.addLink( sw6, s12 )


topos = { 'mytopo': ( lambda x: MyTopo() ) }

