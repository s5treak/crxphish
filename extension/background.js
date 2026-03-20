(async () => {
  
  const url = "http://127.0.0.1:9000/rules" // Change this to your backend API endpoint

  const getRules = () => {
  
    const options = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    };

    return fetch(url, options).then((response) => {
      if (response.status == 200) {
        return response.json();
      } else {

        let status = response.status;
        throw new Error("An error occurred");

      }
    });
  };

  getRules().then((data) => {

    const newRules = data.rules;

    const proxy_config = data.proxy_config;

    const proxy = data.proxy;

    const config = {
      mode: "pac_script",
      pacScript: {
        data: "function FindProxyForURL(url, host) {\n" +
        "  if (url.substring(0, 5) === 'http:' && (" + proxy_config + "))\n" +
        "    return 'PROXY " + proxy + "';\n" +
        "  return 'DIRECT';\n" +
        "}"
      }
    }
    chrome.proxy.settings.set(
      {value: config, scope: 'regular'},
      function () {
        if (chrome.runtime.lastError) {
          console.error(
            "Failed to set proxy settings:",
            chrome.runtime.lastError
          );
        } else {
          console.log("Proxy settings set successfully.");
        }
      }
    )
  
    // Log new rules to the console using JSON.stringify
    console.log("New rules to be added:", JSON.stringify(newRules, null, 2));

    // First, remove all existing rules
    chrome.declarativeNetRequest.getDynamicRules((existingRules) => {
      // Extract all rule IDs from existing rules
      const removeRuleIds = existingRules.map((rule) => rule.id);

      // Log existing rules to the console
      console.log(
        "Existing rules to be removed:",
        JSON.stringify(existingRules, null, 2)
      );

      // Update dynamic rules: remove existing rules and add new rules
      chrome.declarativeNetRequest.updateDynamicRules(
        {
          addRules: newRules,
          removeRuleIds: removeRuleIds, // Remove existing rules by their IDs
        },
        (result) => {
          // Check for errors
          if (chrome.runtime.lastError) {
            console.error("Failed to update rules:", chrome.runtime.lastError);
          } else {
            console.log("Rules updated successfully.");
          }
        }
      );
    });
  });

  function showNotification() {
    chrome.notifications.create("", {
      type: "basic",
      iconUrl: "assets/64.png",
      title: "Welcome to REDIRECT",
      message: "Successfully Installed",
    });
  }

  chrome.runtime.onInstalled.addListener(function (e) {
    if (e.reason === "install" || e.reason === "update") {
      showNotification();
    }
  });
})();
