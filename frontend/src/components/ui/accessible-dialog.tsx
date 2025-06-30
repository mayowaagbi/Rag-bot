import * as React from "react";

interface AccessibleDialogContentProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

export function AccessibleDialogContent({
  children,
  title = "Dialog",
  description = "Dialog content",
  className = "",
  ...props
}: AccessibleDialogContentProps & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={className}
      role="dialog"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
      {...props}
    >
      <div id="dialog-title" className="sr-only">
        {title}
      </div>
      <div id="dialog-description" className="sr-only">
        {description}
      </div>
      {children}
    </div>
  );
}

// HOC to wrap any component that might trigger accessibility warnings
export function withAccessibilityFix<T extends Record<string, any>>(
  Component: React.ComponentType<T>,
  defaultTitle?: string,
  defaultDescription?: string
) {
  return function AccessibleComponent(props: T) {
    return (
      <AccessibleDialogContent
        title={defaultTitle}
        description={defaultDescription}
      >
        <Component {...props} />
      </AccessibleDialogContent>
    );
  };
}
