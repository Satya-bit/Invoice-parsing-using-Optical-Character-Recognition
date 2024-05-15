$("form[name=signup_form]").submit(function(e) {
  e.preventDefault(); // prevent default form submission behavior
  
  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  
  $.ajax({
  url: "/user/signup",
  type: "POST",
  data: data,
  dataType: "json",
  success: function(resp) {
  // Display success message
  $error.removeClass("error--hidden").addClass("success").text("Success! You have successfully signed up.");
  $error.css({ "color": "#4CAF50", "border-color": "#4CAF50" }); // Set the text and border color to green
  $form[0].reset(); // Reset the form on success
  },
  error: function(resp) {
    // Display error message returned by the server
    $error.removeClass("error--hidden").addClass("error").text(resp.responseJSON.error);
    $error.css({ "color": "red", "border-color": "red" }); // Set the text and border color to red
  }
  });
  });
  
  // Handle form submission for login
  $("form[name=login_form]").submit(function(e) {
  e.preventDefault(); // prevent default form submission behavior
  
  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  
  $.ajax({
  url: "/user/login",
  type: "POST",
  data: data,
  dataType: "json",
  success: function(resp) {
  // Redirect to dashboard on success
  window.location.href = "/dashboard/";
  },
  error: function(resp) {
  // Display error message returned by the server
  $error.removeClass("error--hidden").text(resp.responseJSON.error);
  }
  });
  });
  
  // Handle form submission for forgot password
  $("form[name=forgot_password_form]").submit(function(e) {
  e.preventDefault(); // prevent default form submission behavior
  
  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  
  $.ajax({
  url: "/user/forgot_password",
  type: "POST",
  data: data,
  dataType: "json",
  success: function(resp) {
  // Display success message
  $error.removeClass("error--hidden").addClass("success").text(resp.message);
  $error.css({ "color": "#4CAF50", "border-color": "#4CAF50" }); // Set the text and border color to green
  $form[0].reset(); // Reset the form on success
  },
  error: function(resp) {
  // Display error message returned by the server
  $error.removeClass("error--hidden").text(resp.responseJSON.error);
  }
  });
  });
  
  
  
  