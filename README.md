Tries to update<br/>
`connect(sender, SIGNAL(signalName(args)), receiver, SLOT(slotName(args)), connectionType)`<br/>
to<br/>
```connect(sender, &SenderClass::signalName, receiver, &ReceiverClass::slotName, connectionType)```<br/>
for better static checking.

Not meant to be comprehensive, but maybe good enough for a first pass.
