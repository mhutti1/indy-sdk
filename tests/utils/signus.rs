use std::sync::mpsc::{channel};
use std::ffi::{CString};

use sovrin::api::signus::{
    sovrin_create_and_store_my_did,
    sovrin_store_their_did,
};
use sovrin::api::ErrorCode;

use utils::callback::CallbackUtils;
use utils::timeout::TimeoutUtils;

pub struct SignusUtils {}

impl SignusUtils {
    pub fn create_and_store_my_did(wallet_handle: i32, seed: Option<String>) -> Result<(String, String, String), ErrorCode> {
        let (create_and_store_my_did_sender, create_and_store_my_did_receiver) = channel();
        let create_and_store_my_did_cb = Box::new(move |err, did, verkey, public_key| {
            create_and_store_my_did_sender.send((err, did, verkey, public_key)).unwrap();
        });
        let (create_and_store_my_did_command_handle, create_and_store_my_did_callback) = CallbackUtils::closure_to_create_and_store_my_did_cb(create_and_store_my_did_cb);

        let my_did_json = seed.map_or("{}".to_string(), |seed| format!("{{\"seed\":\"{}\" }}", seed));
        let err =
            sovrin_create_and_store_my_did(create_and_store_my_did_command_handle,
                                           wallet_handle,
                                           CString::new(my_did_json).unwrap().as_ptr(),
                                           create_and_store_my_did_callback);

        if err != ErrorCode::Success {
            return Err(err);
        }
        let (err, my_did, my_verkey, my_pk) = create_and_store_my_did_receiver.recv_timeout(TimeoutUtils::long_timeout()).unwrap();
        if err != ErrorCode::Success {
            return Err(err);
        }
        Ok((my_did, my_verkey, my_pk))
    }

    pub fn store_their_did(wallet_handle: i32, their_did: &str, their_pk: &str, their_verkey: &str, endpoint: &str) -> Result<(), ErrorCode> {
        let (store_their_did_sender, store_their_did_receiver) = channel();
        let store_their_did_cb = Box::new(move |err| { store_their_did_sender.send((err)).unwrap(); });
        let (store_their_did_command_handle, store_their_did_callback) = CallbackUtils::closure_to_store_their_did_cb(store_their_did_cb);

        let their_identity_json = format!("{{\"did\":\"{}\",\
                                            \"pk\":\"{}\",\
                                            \"verkey\":\"{}\",\
                                            \"endpoint\":\"{}\"\
                                           }}",
                                          their_did, their_pk, their_verkey, endpoint);
        let err =
            sovrin_store_their_did(store_their_did_command_handle,
                                   wallet_handle,
                                   CString::new(their_identity_json).unwrap().as_ptr(),
                                   store_their_did_callback);

        if err != ErrorCode::Success {
            return Err(err);
        }
        let err = store_their_did_receiver.recv_timeout(TimeoutUtils::long_timeout()).unwrap();
        if err != ErrorCode::Success {
            return Err(err);
        }
        Ok(())
    }
}