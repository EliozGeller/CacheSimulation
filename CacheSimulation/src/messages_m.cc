//
// Generated file, do not edit! Created by nedtool 5.6 from messages.msg.
//

// Disable warnings about unused variables, empty switch stmts, etc:
#ifdef _MSC_VER
#  pragma warning(disable:4101)
#  pragma warning(disable:4065)
#endif

#if defined(__clang__)
#  pragma clang diagnostic ignored "-Wshadow"
#  pragma clang diagnostic ignored "-Wconversion"
#  pragma clang diagnostic ignored "-Wunused-parameter"
#  pragma clang diagnostic ignored "-Wc++98-compat"
#  pragma clang diagnostic ignored "-Wunreachable-code-break"
#  pragma clang diagnostic ignored "-Wold-style-cast"
#elif defined(__GNUC__)
#  pragma GCC diagnostic ignored "-Wshadow"
#  pragma GCC diagnostic ignored "-Wconversion"
#  pragma GCC diagnostic ignored "-Wunused-parameter"
#  pragma GCC diagnostic ignored "-Wold-style-cast"
#  pragma GCC diagnostic ignored "-Wsuggest-attribute=noreturn"
#  pragma GCC diagnostic ignored "-Wfloat-conversion"
#endif

#include <iostream>
#include <sstream>
#include "messages_m.h"

namespace omnetpp {

// Template pack/unpack rules. They are declared *after* a1l type-specific pack functions for multiple reasons.
// They are in the omnetpp namespace, to allow them to be found by argument-dependent lookup via the cCommBuffer argument

// Packing/unpacking an std::vector
template<typename T, typename A>
void doParsimPacking(omnetpp::cCommBuffer *buffer, const std::vector<T,A>& v)
{
    int n = v.size();
    doParsimPacking(buffer, n);
    for (int i = 0; i < n; i++)
        doParsimPacking(buffer, v[i]);
}

template<typename T, typename A>
void doParsimUnpacking(omnetpp::cCommBuffer *buffer, std::vector<T,A>& v)
{
    int n;
    doParsimUnpacking(buffer, n);
    v.resize(n);
    for (int i = 0; i < n; i++)
        doParsimUnpacking(buffer, v[i]);
}

// Packing/unpacking an std::list
template<typename T, typename A>
void doParsimPacking(omnetpp::cCommBuffer *buffer, const std::list<T,A>& l)
{
    doParsimPacking(buffer, (int)l.size());
    for (typename std::list<T,A>::const_iterator it = l.begin(); it != l.end(); ++it)
        doParsimPacking(buffer, (T&)*it);
}

template<typename T, typename A>
void doParsimUnpacking(omnetpp::cCommBuffer *buffer, std::list<T,A>& l)
{
    int n;
    doParsimUnpacking(buffer, n);
    for (int i=0; i<n; i++) {
        l.push_back(T());
        doParsimUnpacking(buffer, l.back());
    }
}

// Packing/unpacking an std::set
template<typename T, typename Tr, typename A>
void doParsimPacking(omnetpp::cCommBuffer *buffer, const std::set<T,Tr,A>& s)
{
    doParsimPacking(buffer, (int)s.size());
    for (typename std::set<T,Tr,A>::const_iterator it = s.begin(); it != s.end(); ++it)
        doParsimPacking(buffer, *it);
}

template<typename T, typename Tr, typename A>
void doParsimUnpacking(omnetpp::cCommBuffer *buffer, std::set<T,Tr,A>& s)
{
    int n;
    doParsimUnpacking(buffer, n);
    for (int i=0; i<n; i++) {
        T x;
        doParsimUnpacking(buffer, x);
        s.insert(x);
    }
}

// Packing/unpacking an std::map
template<typename K, typename V, typename Tr, typename A>
void doParsimPacking(omnetpp::cCommBuffer *buffer, const std::map<K,V,Tr,A>& m)
{
    doParsimPacking(buffer, (int)m.size());
    for (typename std::map<K,V,Tr,A>::const_iterator it = m.begin(); it != m.end(); ++it) {
        doParsimPacking(buffer, it->first);
        doParsimPacking(buffer, it->second);
    }
}

template<typename K, typename V, typename Tr, typename A>
void doParsimUnpacking(omnetpp::cCommBuffer *buffer, std::map<K,V,Tr,A>& m)
{
    int n;
    doParsimUnpacking(buffer, n);
    for (int i=0; i<n; i++) {
        K k; V v;
        doParsimUnpacking(buffer, k);
        doParsimUnpacking(buffer, v);
        m[k] = v;
    }
}

// Default pack/unpack function for arrays
template<typename T>
void doParsimArrayPacking(omnetpp::cCommBuffer *b, const T *t, int n)
{
    for (int i = 0; i < n; i++)
        doParsimPacking(b, t[i]);
}

template<typename T>
void doParsimArrayUnpacking(omnetpp::cCommBuffer *b, T *t, int n)
{
    for (int i = 0; i < n; i++)
        doParsimUnpacking(b, t[i]);
}

// Default rule to prevent compiler from choosing base class' doParsimPacking() function
template<typename T>
void doParsimPacking(omnetpp::cCommBuffer *, const T& t)
{
    throw omnetpp::cRuntimeError("Parsim error: No doParsimPacking() function for type %s", omnetpp::opp_typename(typeid(t)));
}

template<typename T>
void doParsimUnpacking(omnetpp::cCommBuffer *, T& t)
{
    throw omnetpp::cRuntimeError("Parsim error: No doParsimUnpacking() function for type %s", omnetpp::opp_typename(typeid(t)));
}

}  // namespace omnetpp

namespace cachesimulation {

// forward
template<typename T, typename A>
std::ostream& operator<<(std::ostream& out, const std::vector<T,A>& vec);

// Template rule which fires if a struct or class doesn't have operator<<
template<typename T>
inline std::ostream& operator<<(std::ostream& out,const T&) {return out;}

// operator<< for std::vector<T>
template<typename T, typename A>
inline std::ostream& operator<<(std::ostream& out, const std::vector<T,A>& vec)
{
    out.put('{');
    for(typename std::vector<T,A>::const_iterator it = vec.begin(); it != vec.end(); ++it)
    {
        if (it != vec.begin()) {
            out.put(','); out.put(' ');
        }
        out << *it;
    }
    out.put('}');
    
    char buf[32];
    sprintf(buf, " (size=%u)", (unsigned int)vec.size());
    out.write(buf, strlen(buf));
    return out;
}

Register_Class(DataPacket)

DataPacket::DataPacket(const char *name, short kind) : ::omnetpp::cPacket(name,kind)
{
    this->destination = 0;
    this->external_destination = 0;
    this->miss_hop = 0;
    this->request = 0;
}

DataPacket::DataPacket(const DataPacket& other) : ::omnetpp::cPacket(other)
{
    copy(other);
}

DataPacket::~DataPacket()
{
}

DataPacket& DataPacket::operator=(const DataPacket& other)
{
    if (this==&other) return *this;
    ::omnetpp::cPacket::operator=(other);
    copy(other);
    return *this;
}

void DataPacket::copy(const DataPacket& other)
{
    this->destination = other.destination;
    this->external_destination = other.external_destination;
    this->miss_hop = other.miss_hop;
    this->id = other.id;
    this->request = other.request;
}

void DataPacket::parsimPack(omnetpp::cCommBuffer *b) const
{
    ::omnetpp::cPacket::parsimPack(b);
    doParsimPacking(b,this->destination);
    doParsimPacking(b,this->external_destination);
    doParsimPacking(b,this->miss_hop);
    doParsimPacking(b,this->id);
    doParsimPacking(b,this->request);
}

void DataPacket::parsimUnpack(omnetpp::cCommBuffer *b)
{
    ::omnetpp::cPacket::parsimUnpack(b);
    doParsimUnpacking(b,this->destination);
    doParsimUnpacking(b,this->external_destination);
    doParsimUnpacking(b,this->miss_hop);
    doParsimUnpacking(b,this->id);
    doParsimUnpacking(b,this->request);
}

uint64_t DataPacket::getDestination() const
{
    return this->destination;
}

void DataPacket::setDestination(uint64_t destination)
{
    this->destination = destination;
}

uint64_t DataPacket::getExternal_destination() const
{
    return this->external_destination;
}

void DataPacket::setExternal_destination(uint64_t external_destination)
{
    this->external_destination = external_destination;
}

int DataPacket::getMiss_hop() const
{
    return this->miss_hop;
}

void DataPacket::setMiss_hop(int miss_hop)
{
    this->miss_hop = miss_hop;
}

const char * DataPacket::getId() const
{
    return this->id.c_str();
}

void DataPacket::setId(const char * id)
{
    this->id = id;
}

int DataPacket::getRequest() const
{
    return this->request;
}

void DataPacket::setRequest(int request)
{
    this->request = request;
}

class DataPacketDescriptor : public omnetpp::cClassDescriptor
{
  private:
    mutable const char **propertynames;
  public:
    DataPacketDescriptor();
    virtual ~DataPacketDescriptor();

    virtual bool doesSupport(omnetpp::cObject *obj) const override;
    virtual const char **getPropertyNames() const override;
    virtual const char *getProperty(const char *propertyname) const override;
    virtual int getFieldCount() const override;
    virtual const char *getFieldName(int field) const override;
    virtual int findField(const char *fieldName) const override;
    virtual unsigned int getFieldTypeFlags(int field) const override;
    virtual const char *getFieldTypeString(int field) const override;
    virtual const char **getFieldPropertyNames(int field) const override;
    virtual const char *getFieldProperty(int field, const char *propertyname) const override;
    virtual int getFieldArraySize(void *object, int field) const override;

    virtual const char *getFieldDynamicTypeString(void *object, int field, int i) const override;
    virtual std::string getFieldValueAsString(void *object, int field, int i) const override;
    virtual bool setFieldValueAsString(void *object, int field, int i, const char *value) const override;

    virtual const char *getFieldStructName(int field) const override;
    virtual void *getFieldStructValuePointer(void *object, int field, int i) const override;
};

Register_ClassDescriptor(DataPacketDescriptor)

DataPacketDescriptor::DataPacketDescriptor() : omnetpp::cClassDescriptor("cachesimulation::DataPacket", "omnetpp::cPacket")
{
    propertynames = nullptr;
}

DataPacketDescriptor::~DataPacketDescriptor()
{
    delete[] propertynames;
}

bool DataPacketDescriptor::doesSupport(omnetpp::cObject *obj) const
{
    return dynamic_cast<DataPacket *>(obj)!=nullptr;
}

const char **DataPacketDescriptor::getPropertyNames() const
{
    if (!propertynames) {
        static const char *names[] = {  nullptr };
        omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
        const char **basenames = basedesc ? basedesc->getPropertyNames() : nullptr;
        propertynames = mergeLists(basenames, names);
    }
    return propertynames;
}

const char *DataPacketDescriptor::getProperty(const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : nullptr;
}

int DataPacketDescriptor::getFieldCount() const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 5+basedesc->getFieldCount() : 5;
}

unsigned int DataPacketDescriptor::getFieldTypeFlags(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeFlags(field);
        field -= basedesc->getFieldCount();
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
    };
    return (field>=0 && field<5) ? fieldTypeFlags[field] : 0;
}

const char *DataPacketDescriptor::getFieldName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldName(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldNames[] = {
        "destination",
        "external_destination",
        "miss_hop",
        "id",
        "request",
    };
    return (field>=0 && field<5) ? fieldNames[field] : nullptr;
}

int DataPacketDescriptor::findField(const char *fieldName) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount() : 0;
    if (fieldName[0]=='d' && strcmp(fieldName, "destination")==0) return base+0;
    if (fieldName[0]=='e' && strcmp(fieldName, "external_destination")==0) return base+1;
    if (fieldName[0]=='m' && strcmp(fieldName, "miss_hop")==0) return base+2;
    if (fieldName[0]=='i' && strcmp(fieldName, "id")==0) return base+3;
    if (fieldName[0]=='r' && strcmp(fieldName, "request")==0) return base+4;
    return basedesc ? basedesc->findField(fieldName) : -1;
}

const char *DataPacketDescriptor::getFieldTypeString(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeString(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldTypeStrings[] = {
        "uint64_t",
        "uint64_t",
        "int",
        "string",
        "int",
    };
    return (field>=0 && field<5) ? fieldTypeStrings[field] : nullptr;
}

const char **DataPacketDescriptor::getFieldPropertyNames(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldPropertyNames(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

const char *DataPacketDescriptor::getFieldProperty(int field, const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldProperty(field, propertyname);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

int DataPacketDescriptor::getFieldArraySize(void *object, int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldArraySize(object, field);
        field -= basedesc->getFieldCount();
    }
    DataPacket *pp = (DataPacket *)object; (void)pp;
    switch (field) {
        default: return 0;
    }
}

const char *DataPacketDescriptor::getFieldDynamicTypeString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldDynamicTypeString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    DataPacket *pp = (DataPacket *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

std::string DataPacketDescriptor::getFieldValueAsString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldValueAsString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    DataPacket *pp = (DataPacket *)object; (void)pp;
    switch (field) {
        case 0: return uint642string(pp->getDestination());
        case 1: return uint642string(pp->getExternal_destination());
        case 2: return long2string(pp->getMiss_hop());
        case 3: return oppstring2string(pp->getId());
        case 4: return long2string(pp->getRequest());
        default: return "";
    }
}

bool DataPacketDescriptor::setFieldValueAsString(void *object, int field, int i, const char *value) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->setFieldValueAsString(object,field,i,value);
        field -= basedesc->getFieldCount();
    }
    DataPacket *pp = (DataPacket *)object; (void)pp;
    switch (field) {
        case 0: pp->setDestination(string2uint64(value)); return true;
        case 1: pp->setExternal_destination(string2uint64(value)); return true;
        case 2: pp->setMiss_hop(string2long(value)); return true;
        case 3: pp->setId((value)); return true;
        case 4: pp->setRequest(string2long(value)); return true;
        default: return false;
    }
}

const char *DataPacketDescriptor::getFieldStructName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructName(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    };
}

void *DataPacketDescriptor::getFieldStructValuePointer(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructValuePointer(object, field, i);
        field -= basedesc->getFieldCount();
    }
    DataPacket *pp = (DataPacket *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

Register_Class(InsertionPacket)

InsertionPacket::InsertionPacket(const char *name, short kind) : ::omnetpp::cPacket(name,kind)
{
    this->rule = 0;
    this->type = 0;
    this->switch_type = 0;
    this->destination = 0;
}

InsertionPacket::InsertionPacket(const InsertionPacket& other) : ::omnetpp::cPacket(other)
{
    copy(other);
}

InsertionPacket::~InsertionPacket()
{
}

InsertionPacket& InsertionPacket::operator=(const InsertionPacket& other)
{
    if (this==&other) return *this;
    ::omnetpp::cPacket::operator=(other);
    copy(other);
    return *this;
}

void InsertionPacket::copy(const InsertionPacket& other)
{
    this->rule = other.rule;
    this->type = other.type;
    this->switch_type = other.switch_type;
    this->destination = other.destination;
}

void InsertionPacket::parsimPack(omnetpp::cCommBuffer *b) const
{
    ::omnetpp::cPacket::parsimPack(b);
    doParsimPacking(b,this->rule);
    doParsimPacking(b,this->type);
    doParsimPacking(b,this->switch_type);
    doParsimPacking(b,this->destination);
}

void InsertionPacket::parsimUnpack(omnetpp::cCommBuffer *b)
{
    ::omnetpp::cPacket::parsimUnpack(b);
    doParsimUnpacking(b,this->rule);
    doParsimUnpacking(b,this->type);
    doParsimUnpacking(b,this->switch_type);
    doParsimUnpacking(b,this->destination);
}

uint64_t InsertionPacket::getRule() const
{
    return this->rule;
}

void InsertionPacket::setRule(uint64_t rule)
{
    this->rule = rule;
}

int InsertionPacket::getType() const
{
    return this->type;
}

void InsertionPacket::setType(int type)
{
    this->type = type;
}

int InsertionPacket::getSwitch_type() const
{
    return this->switch_type;
}

void InsertionPacket::setSwitch_type(int switch_type)
{
    this->switch_type = switch_type;
}

int InsertionPacket::getDestination() const
{
    return this->destination;
}

void InsertionPacket::setDestination(int destination)
{
    this->destination = destination;
}

class InsertionPacketDescriptor : public omnetpp::cClassDescriptor
{
  private:
    mutable const char **propertynames;
  public:
    InsertionPacketDescriptor();
    virtual ~InsertionPacketDescriptor();

    virtual bool doesSupport(omnetpp::cObject *obj) const override;
    virtual const char **getPropertyNames() const override;
    virtual const char *getProperty(const char *propertyname) const override;
    virtual int getFieldCount() const override;
    virtual const char *getFieldName(int field) const override;
    virtual int findField(const char *fieldName) const override;
    virtual unsigned int getFieldTypeFlags(int field) const override;
    virtual const char *getFieldTypeString(int field) const override;
    virtual const char **getFieldPropertyNames(int field) const override;
    virtual const char *getFieldProperty(int field, const char *propertyname) const override;
    virtual int getFieldArraySize(void *object, int field) const override;

    virtual const char *getFieldDynamicTypeString(void *object, int field, int i) const override;
    virtual std::string getFieldValueAsString(void *object, int field, int i) const override;
    virtual bool setFieldValueAsString(void *object, int field, int i, const char *value) const override;

    virtual const char *getFieldStructName(int field) const override;
    virtual void *getFieldStructValuePointer(void *object, int field, int i) const override;
};

Register_ClassDescriptor(InsertionPacketDescriptor)

InsertionPacketDescriptor::InsertionPacketDescriptor() : omnetpp::cClassDescriptor("cachesimulation::InsertionPacket", "omnetpp::cPacket")
{
    propertynames = nullptr;
}

InsertionPacketDescriptor::~InsertionPacketDescriptor()
{
    delete[] propertynames;
}

bool InsertionPacketDescriptor::doesSupport(omnetpp::cObject *obj) const
{
    return dynamic_cast<InsertionPacket *>(obj)!=nullptr;
}

const char **InsertionPacketDescriptor::getPropertyNames() const
{
    if (!propertynames) {
        static const char *names[] = {  nullptr };
        omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
        const char **basenames = basedesc ? basedesc->getPropertyNames() : nullptr;
        propertynames = mergeLists(basenames, names);
    }
    return propertynames;
}

const char *InsertionPacketDescriptor::getProperty(const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : nullptr;
}

int InsertionPacketDescriptor::getFieldCount() const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 4+basedesc->getFieldCount() : 4;
}

unsigned int InsertionPacketDescriptor::getFieldTypeFlags(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeFlags(field);
        field -= basedesc->getFieldCount();
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
        FD_ISEDITABLE,
    };
    return (field>=0 && field<4) ? fieldTypeFlags[field] : 0;
}

const char *InsertionPacketDescriptor::getFieldName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldName(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldNames[] = {
        "rule",
        "type",
        "switch_type",
        "destination",
    };
    return (field>=0 && field<4) ? fieldNames[field] : nullptr;
}

int InsertionPacketDescriptor::findField(const char *fieldName) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount() : 0;
    if (fieldName[0]=='r' && strcmp(fieldName, "rule")==0) return base+0;
    if (fieldName[0]=='t' && strcmp(fieldName, "type")==0) return base+1;
    if (fieldName[0]=='s' && strcmp(fieldName, "switch_type")==0) return base+2;
    if (fieldName[0]=='d' && strcmp(fieldName, "destination")==0) return base+3;
    return basedesc ? basedesc->findField(fieldName) : -1;
}

const char *InsertionPacketDescriptor::getFieldTypeString(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeString(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldTypeStrings[] = {
        "uint64_t",
        "int",
        "int",
        "int",
    };
    return (field>=0 && field<4) ? fieldTypeStrings[field] : nullptr;
}

const char **InsertionPacketDescriptor::getFieldPropertyNames(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldPropertyNames(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

const char *InsertionPacketDescriptor::getFieldProperty(int field, const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldProperty(field, propertyname);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

int InsertionPacketDescriptor::getFieldArraySize(void *object, int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldArraySize(object, field);
        field -= basedesc->getFieldCount();
    }
    InsertionPacket *pp = (InsertionPacket *)object; (void)pp;
    switch (field) {
        default: return 0;
    }
}

const char *InsertionPacketDescriptor::getFieldDynamicTypeString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldDynamicTypeString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    InsertionPacket *pp = (InsertionPacket *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

std::string InsertionPacketDescriptor::getFieldValueAsString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldValueAsString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    InsertionPacket *pp = (InsertionPacket *)object; (void)pp;
    switch (field) {
        case 0: return uint642string(pp->getRule());
        case 1: return long2string(pp->getType());
        case 2: return long2string(pp->getSwitch_type());
        case 3: return long2string(pp->getDestination());
        default: return "";
    }
}

bool InsertionPacketDescriptor::setFieldValueAsString(void *object, int field, int i, const char *value) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->setFieldValueAsString(object,field,i,value);
        field -= basedesc->getFieldCount();
    }
    InsertionPacket *pp = (InsertionPacket *)object; (void)pp;
    switch (field) {
        case 0: pp->setRule(string2uint64(value)); return true;
        case 1: pp->setType(string2long(value)); return true;
        case 2: pp->setSwitch_type(string2long(value)); return true;
        case 3: pp->setDestination(string2long(value)); return true;
        default: return false;
    }
}

const char *InsertionPacketDescriptor::getFieldStructName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructName(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    };
}

void *InsertionPacketDescriptor::getFieldStructValuePointer(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructValuePointer(object, field, i);
        field -= basedesc->getFieldCount();
    }
    InsertionPacket *pp = (InsertionPacket *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

Register_Class(Data_for_partition)

Data_for_partition::Data_for_partition(const char *name, short kind) : ::omnetpp::cPacket(name,kind)
{
    for (unsigned int i=0; i<100; i++)
        this->counters[i] = 0;
}

Data_for_partition::Data_for_partition(const Data_for_partition& other) : ::omnetpp::cPacket(other)
{
    copy(other);
}

Data_for_partition::~Data_for_partition()
{
}

Data_for_partition& Data_for_partition::operator=(const Data_for_partition& other)
{
    if (this==&other) return *this;
    ::omnetpp::cPacket::operator=(other);
    copy(other);
    return *this;
}

void Data_for_partition::copy(const Data_for_partition& other)
{
    for (unsigned int i=0; i<100; i++)
        this->counters[i] = other.counters[i];
}

void Data_for_partition::parsimPack(omnetpp::cCommBuffer *b) const
{
    ::omnetpp::cPacket::parsimPack(b);
    doParsimArrayPacking(b,this->counters,100);
}

void Data_for_partition::parsimUnpack(omnetpp::cCommBuffer *b)
{
    ::omnetpp::cPacket::parsimUnpack(b);
    doParsimArrayUnpacking(b,this->counters,100);
}

unsigned int Data_for_partition::getCountersArraySize() const
{
    return 100;
}

uint64_t Data_for_partition::getCounters(unsigned int k) const
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    return this->counters[k];
}

void Data_for_partition::setCounters(unsigned int k, uint64_t counters)
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    this->counters[k] = counters;
}

class Data_for_partitionDescriptor : public omnetpp::cClassDescriptor
{
  private:
    mutable const char **propertynames;
  public:
    Data_for_partitionDescriptor();
    virtual ~Data_for_partitionDescriptor();

    virtual bool doesSupport(omnetpp::cObject *obj) const override;
    virtual const char **getPropertyNames() const override;
    virtual const char *getProperty(const char *propertyname) const override;
    virtual int getFieldCount() const override;
    virtual const char *getFieldName(int field) const override;
    virtual int findField(const char *fieldName) const override;
    virtual unsigned int getFieldTypeFlags(int field) const override;
    virtual const char *getFieldTypeString(int field) const override;
    virtual const char **getFieldPropertyNames(int field) const override;
    virtual const char *getFieldProperty(int field, const char *propertyname) const override;
    virtual int getFieldArraySize(void *object, int field) const override;

    virtual const char *getFieldDynamicTypeString(void *object, int field, int i) const override;
    virtual std::string getFieldValueAsString(void *object, int field, int i) const override;
    virtual bool setFieldValueAsString(void *object, int field, int i, const char *value) const override;

    virtual const char *getFieldStructName(int field) const override;
    virtual void *getFieldStructValuePointer(void *object, int field, int i) const override;
};

Register_ClassDescriptor(Data_for_partitionDescriptor)

Data_for_partitionDescriptor::Data_for_partitionDescriptor() : omnetpp::cClassDescriptor("cachesimulation::Data_for_partition", "omnetpp::cPacket")
{
    propertynames = nullptr;
}

Data_for_partitionDescriptor::~Data_for_partitionDescriptor()
{
    delete[] propertynames;
}

bool Data_for_partitionDescriptor::doesSupport(omnetpp::cObject *obj) const
{
    return dynamic_cast<Data_for_partition *>(obj)!=nullptr;
}

const char **Data_for_partitionDescriptor::getPropertyNames() const
{
    if (!propertynames) {
        static const char *names[] = {  nullptr };
        omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
        const char **basenames = basedesc ? basedesc->getPropertyNames() : nullptr;
        propertynames = mergeLists(basenames, names);
    }
    return propertynames;
}

const char *Data_for_partitionDescriptor::getProperty(const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : nullptr;
}

int Data_for_partitionDescriptor::getFieldCount() const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 1+basedesc->getFieldCount() : 1;
}

unsigned int Data_for_partitionDescriptor::getFieldTypeFlags(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeFlags(field);
        field -= basedesc->getFieldCount();
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISARRAY | FD_ISEDITABLE,
    };
    return (field>=0 && field<1) ? fieldTypeFlags[field] : 0;
}

const char *Data_for_partitionDescriptor::getFieldName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldName(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldNames[] = {
        "counters",
    };
    return (field>=0 && field<1) ? fieldNames[field] : nullptr;
}

int Data_for_partitionDescriptor::findField(const char *fieldName) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount() : 0;
    if (fieldName[0]=='c' && strcmp(fieldName, "counters")==0) return base+0;
    return basedesc ? basedesc->findField(fieldName) : -1;
}

const char *Data_for_partitionDescriptor::getFieldTypeString(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeString(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldTypeStrings[] = {
        "uint64_t",
    };
    return (field>=0 && field<1) ? fieldTypeStrings[field] : nullptr;
}

const char **Data_for_partitionDescriptor::getFieldPropertyNames(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldPropertyNames(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

const char *Data_for_partitionDescriptor::getFieldProperty(int field, const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldProperty(field, propertyname);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

int Data_for_partitionDescriptor::getFieldArraySize(void *object, int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldArraySize(object, field);
        field -= basedesc->getFieldCount();
    }
    Data_for_partition *pp = (Data_for_partition *)object; (void)pp;
    switch (field) {
        case 0: return 100;
        default: return 0;
    }
}

const char *Data_for_partitionDescriptor::getFieldDynamicTypeString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldDynamicTypeString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    Data_for_partition *pp = (Data_for_partition *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

std::string Data_for_partitionDescriptor::getFieldValueAsString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldValueAsString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    Data_for_partition *pp = (Data_for_partition *)object; (void)pp;
    switch (field) {
        case 0: return uint642string(pp->getCounters(i));
        default: return "";
    }
}

bool Data_for_partitionDescriptor::setFieldValueAsString(void *object, int field, int i, const char *value) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->setFieldValueAsString(object,field,i,value);
        field -= basedesc->getFieldCount();
    }
    Data_for_partition *pp = (Data_for_partition *)object; (void)pp;
    switch (field) {
        case 0: pp->setCounters(i,string2uint64(value)); return true;
        default: return false;
    }
}

const char *Data_for_partitionDescriptor::getFieldStructName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructName(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    };
}

void *Data_for_partitionDescriptor::getFieldStructValuePointer(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructValuePointer(object, field, i);
        field -= basedesc->getFieldCount();
    }
    Data_for_partition *pp = (Data_for_partition *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

Register_Class(Partition_update_msg)

Partition_update_msg::Partition_update_msg(const char *name, short kind) : ::omnetpp::cPacket(name,kind)
{
    for (unsigned int i=0; i<100; i++)
        this->lows[i] = 0;
    for (unsigned int i=0; i<100; i++)
        this->highs[i] = 0;
    for (unsigned int i=0; i<100; i++)
        this->ports[i] = 0;
}

Partition_update_msg::Partition_update_msg(const Partition_update_msg& other) : ::omnetpp::cPacket(other)
{
    copy(other);
}

Partition_update_msg::~Partition_update_msg()
{
}

Partition_update_msg& Partition_update_msg::operator=(const Partition_update_msg& other)
{
    if (this==&other) return *this;
    ::omnetpp::cPacket::operator=(other);
    copy(other);
    return *this;
}

void Partition_update_msg::copy(const Partition_update_msg& other)
{
    for (unsigned int i=0; i<100; i++)
        this->lows[i] = other.lows[i];
    for (unsigned int i=0; i<100; i++)
        this->highs[i] = other.highs[i];
    for (unsigned int i=0; i<100; i++)
        this->ports[i] = other.ports[i];
}

void Partition_update_msg::parsimPack(omnetpp::cCommBuffer *b) const
{
    ::omnetpp::cPacket::parsimPack(b);
    doParsimArrayPacking(b,this->lows,100);
    doParsimArrayPacking(b,this->highs,100);
    doParsimArrayPacking(b,this->ports,100);
}

void Partition_update_msg::parsimUnpack(omnetpp::cCommBuffer *b)
{
    ::omnetpp::cPacket::parsimUnpack(b);
    doParsimArrayUnpacking(b,this->lows,100);
    doParsimArrayUnpacking(b,this->highs,100);
    doParsimArrayUnpacking(b,this->ports,100);
}

unsigned int Partition_update_msg::getLowsArraySize() const
{
    return 100;
}

uint64_t Partition_update_msg::getLows(unsigned int k) const
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    return this->lows[k];
}

void Partition_update_msg::setLows(unsigned int k, uint64_t lows)
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    this->lows[k] = lows;
}

unsigned int Partition_update_msg::getHighsArraySize() const
{
    return 100;
}

uint64_t Partition_update_msg::getHighs(unsigned int k) const
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    return this->highs[k];
}

void Partition_update_msg::setHighs(unsigned int k, uint64_t highs)
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    this->highs[k] = highs;
}

unsigned int Partition_update_msg::getPortsArraySize() const
{
    return 100;
}

int Partition_update_msg::getPorts(unsigned int k) const
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    return this->ports[k];
}

void Partition_update_msg::setPorts(unsigned int k, int ports)
{
    if (k>=100) throw omnetpp::cRuntimeError("Array of size 100 indexed by %lu", (unsigned long)k);
    this->ports[k] = ports;
}

class Partition_update_msgDescriptor : public omnetpp::cClassDescriptor
{
  private:
    mutable const char **propertynames;
  public:
    Partition_update_msgDescriptor();
    virtual ~Partition_update_msgDescriptor();

    virtual bool doesSupport(omnetpp::cObject *obj) const override;
    virtual const char **getPropertyNames() const override;
    virtual const char *getProperty(const char *propertyname) const override;
    virtual int getFieldCount() const override;
    virtual const char *getFieldName(int field) const override;
    virtual int findField(const char *fieldName) const override;
    virtual unsigned int getFieldTypeFlags(int field) const override;
    virtual const char *getFieldTypeString(int field) const override;
    virtual const char **getFieldPropertyNames(int field) const override;
    virtual const char *getFieldProperty(int field, const char *propertyname) const override;
    virtual int getFieldArraySize(void *object, int field) const override;

    virtual const char *getFieldDynamicTypeString(void *object, int field, int i) const override;
    virtual std::string getFieldValueAsString(void *object, int field, int i) const override;
    virtual bool setFieldValueAsString(void *object, int field, int i, const char *value) const override;

    virtual const char *getFieldStructName(int field) const override;
    virtual void *getFieldStructValuePointer(void *object, int field, int i) const override;
};

Register_ClassDescriptor(Partition_update_msgDescriptor)

Partition_update_msgDescriptor::Partition_update_msgDescriptor() : omnetpp::cClassDescriptor("cachesimulation::Partition_update_msg", "omnetpp::cPacket")
{
    propertynames = nullptr;
}

Partition_update_msgDescriptor::~Partition_update_msgDescriptor()
{
    delete[] propertynames;
}

bool Partition_update_msgDescriptor::doesSupport(omnetpp::cObject *obj) const
{
    return dynamic_cast<Partition_update_msg *>(obj)!=nullptr;
}

const char **Partition_update_msgDescriptor::getPropertyNames() const
{
    if (!propertynames) {
        static const char *names[] = {  nullptr };
        omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
        const char **basenames = basedesc ? basedesc->getPropertyNames() : nullptr;
        propertynames = mergeLists(basenames, names);
    }
    return propertynames;
}

const char *Partition_update_msgDescriptor::getProperty(const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? basedesc->getProperty(propertyname) : nullptr;
}

int Partition_update_msgDescriptor::getFieldCount() const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    return basedesc ? 3+basedesc->getFieldCount() : 3;
}

unsigned int Partition_update_msgDescriptor::getFieldTypeFlags(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeFlags(field);
        field -= basedesc->getFieldCount();
    }
    static unsigned int fieldTypeFlags[] = {
        FD_ISARRAY | FD_ISEDITABLE,
        FD_ISARRAY | FD_ISEDITABLE,
        FD_ISARRAY | FD_ISEDITABLE,
    };
    return (field>=0 && field<3) ? fieldTypeFlags[field] : 0;
}

const char *Partition_update_msgDescriptor::getFieldName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldName(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldNames[] = {
        "lows",
        "highs",
        "ports",
    };
    return (field>=0 && field<3) ? fieldNames[field] : nullptr;
}

int Partition_update_msgDescriptor::findField(const char *fieldName) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    int base = basedesc ? basedesc->getFieldCount() : 0;
    if (fieldName[0]=='l' && strcmp(fieldName, "lows")==0) return base+0;
    if (fieldName[0]=='h' && strcmp(fieldName, "highs")==0) return base+1;
    if (fieldName[0]=='p' && strcmp(fieldName, "ports")==0) return base+2;
    return basedesc ? basedesc->findField(fieldName) : -1;
}

const char *Partition_update_msgDescriptor::getFieldTypeString(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldTypeString(field);
        field -= basedesc->getFieldCount();
    }
    static const char *fieldTypeStrings[] = {
        "uint64_t",
        "uint64_t",
        "int",
    };
    return (field>=0 && field<3) ? fieldTypeStrings[field] : nullptr;
}

const char **Partition_update_msgDescriptor::getFieldPropertyNames(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldPropertyNames(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

const char *Partition_update_msgDescriptor::getFieldProperty(int field, const char *propertyname) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldProperty(field, propertyname);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    }
}

int Partition_update_msgDescriptor::getFieldArraySize(void *object, int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldArraySize(object, field);
        field -= basedesc->getFieldCount();
    }
    Partition_update_msg *pp = (Partition_update_msg *)object; (void)pp;
    switch (field) {
        case 0: return 100;
        case 1: return 100;
        case 2: return 100;
        default: return 0;
    }
}

const char *Partition_update_msgDescriptor::getFieldDynamicTypeString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldDynamicTypeString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    Partition_update_msg *pp = (Partition_update_msg *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

std::string Partition_update_msgDescriptor::getFieldValueAsString(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldValueAsString(object,field,i);
        field -= basedesc->getFieldCount();
    }
    Partition_update_msg *pp = (Partition_update_msg *)object; (void)pp;
    switch (field) {
        case 0: return uint642string(pp->getLows(i));
        case 1: return uint642string(pp->getHighs(i));
        case 2: return long2string(pp->getPorts(i));
        default: return "";
    }
}

bool Partition_update_msgDescriptor::setFieldValueAsString(void *object, int field, int i, const char *value) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->setFieldValueAsString(object,field,i,value);
        field -= basedesc->getFieldCount();
    }
    Partition_update_msg *pp = (Partition_update_msg *)object; (void)pp;
    switch (field) {
        case 0: pp->setLows(i,string2uint64(value)); return true;
        case 1: pp->setHighs(i,string2uint64(value)); return true;
        case 2: pp->setPorts(i,string2long(value)); return true;
        default: return false;
    }
}

const char *Partition_update_msgDescriptor::getFieldStructName(int field) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructName(field);
        field -= basedesc->getFieldCount();
    }
    switch (field) {
        default: return nullptr;
    };
}

void *Partition_update_msgDescriptor::getFieldStructValuePointer(void *object, int field, int i) const
{
    omnetpp::cClassDescriptor *basedesc = getBaseClassDescriptor();
    if (basedesc) {
        if (field < basedesc->getFieldCount())
            return basedesc->getFieldStructValuePointer(object, field, i);
        field -= basedesc->getFieldCount();
    }
    Partition_update_msg *pp = (Partition_update_msg *)object; (void)pp;
    switch (field) {
        default: return nullptr;
    }
}

} // namespace cachesimulation

