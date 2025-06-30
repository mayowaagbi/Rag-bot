import { useEffect } from "react";

export function useDialogAccessibilityFix() {
  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === "childList") {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node as Element;

              // Check for dialog content elements
              const dialogContent =
                element.querySelector("[data-radix-dialog-content]") ||
                element.querySelector('[data-slot="sheet-content"]') ||
                (element.getAttribute("data-radix-dialog-content") !== null
                  ? element
                  : null) ||
                (element.getAttribute("data-slot") === "sheet-content"
                  ? element
                  : null);

              if (dialogContent) {
                // Check if it has a title
                const hasTitle =
                  dialogContent.querySelector("[data-radix-dialog-title]") ||
                  dialogContent.querySelector('[data-slot="sheet-title"]');

                if (!hasTitle) {
                  // Create and add a visually hidden title
                  const title = document.createElement("div");
                  title.setAttribute("data-radix-dialog-title", "");
                  title.className = "sr-only";
                  title.textContent = "Dialog";
                  dialogContent.prepend(title);
                }

                // Check if it has a description
                const hasDescription =
                  dialogContent.querySelector(
                    "[data-radix-dialog-description]"
                  ) ||
                  dialogContent.querySelector(
                    '[data-slot="sheet-description"]'
                  );

                if (!hasDescription) {
                  // Create and add a visually hidden description
                  const description = document.createElement("div");
                  description.setAttribute("data-radix-dialog-description", "");
                  description.className = "sr-only";
                  description.textContent = "Dialog content";

                  // Insert after title if it exists
                  const title =
                    dialogContent.querySelector("[data-radix-dialog-title]") ||
                    dialogContent.querySelector('[data-slot="sheet-title"]');

                  if (title && title.nextSibling) {
                    title.parentNode?.insertBefore(
                      description,
                      title.nextSibling
                    );
                  } else {
                    dialogContent.prepend(description);
                  }
                }
              }
            }
          });
        }
      });
    });

    // Start observing
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // Also fix any existing dialogs
    const existingDialogs = document.querySelectorAll(
      '[data-radix-dialog-content], [data-slot="sheet-content"]'
    );
    existingDialogs.forEach((dialog) => {
      const hasTitle = dialog.querySelector(
        '[data-radix-dialog-title], [data-slot="sheet-title"]'
      );
      if (!hasTitle) {
        const title = document.createElement("div");
        title.setAttribute("data-radix-dialog-title", "");
        title.className = "sr-only";
        title.textContent = "Dialog";
        dialog.prepend(title);
      }

      const hasDescription = dialog.querySelector(
        '[data-radix-dialog-description], [data-slot="sheet-description"]'
      );
      if (!hasDescription) {
        const description = document.createElement("div");
        description.setAttribute("data-radix-dialog-description", "");
        description.className = "sr-only";
        description.textContent = "Dialog content";
        dialog.prepend(description);
      }
    });

    return () => observer.disconnect();
  }, []);
}

export default useDialogAccessibilityFix;
