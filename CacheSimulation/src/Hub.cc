//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#ifndef __CACHESIMULATION_TCX_H
#define __CACHESIMULATION_TCX_H

#include <omnetpp.h>
#include "messages_m.h"

using namespace omnetpp;

namespace cachesimulation {

/**
 * Implements the Txc simple module. See the NED file for more information.
 */
class Hub : public cSimpleModule
{
private:
  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
};

}; // namespace

#endif




namespace cachesimulation {

Define_Module(Hub);

void Hub::initialize()
{

}

void Hub::handleMessage(cMessage *message)
{
    send(message, "port$o", 0);
}
}; // namespace
