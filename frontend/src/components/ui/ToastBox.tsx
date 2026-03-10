import { ToastContainer } from "react-toastify";
function ToastBox() {
  return (
    <ToastContainer
      position="top-right"
      autoClose={2000}
      hideProgressBar={false}
      newestOnTop={true}
      closeOnClick
      rtl={false}
      pauseOnFocusLoss
      draggable
      pauseOnHover
    />
  );
}

export default ToastBox;
