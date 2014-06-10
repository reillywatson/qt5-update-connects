Tries to update connect(sender, SIGNAL(signalName(args)), receiver, SLOT(slotName(args)), connectionType) to be connect(sender, &SenderClass::signalName, receiver, &ReceiverClass::slotName, connectionType), for better static checking.

Not meant to be comprehensive, but maybe good enough for a first pass.
