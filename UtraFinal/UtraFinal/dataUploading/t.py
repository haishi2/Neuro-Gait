import pymongo


# put this in the flask api file so it doessn't need to be rerun



#create patient with patient object, initialize recordings to empty list, gait_info set every float to 0 (IN BACKEND DO NOT USE THIS IN THE RUNNING AVERAGE, JUST TAKE THE FIRST RUN AS THE NEW AVERAGE), item_count to 0
def create_patient(patient, collection):
    collection.insert_one(patient)

#return a list of all patient names 
def get_patient_names(collection):
    return [patient["Name"] for patient in collection.find({}, {"Name": 1})]


# return a patient object
def get_patient(patient_name, collection):
    return collection.find_one({"Name": patient_name}, {"_id": 0})


#ONLY UPDATES THE PATIENT
# BACKEND: append a new recording to Recordings, update item_count, update any user info, update gait_info
def update_patient_info(new_patient, new_name, collection):
    query = {"Name": new_patient["Name"]} 

    if new_name:
        new_patient["Name"] = new_name

    update = {"$set": new_patient}
    collection.update_one(query, update)
    
#delete patient
def delete_patient(patient_name, collection):
    collection.delete_one({"Name": patient_name})



