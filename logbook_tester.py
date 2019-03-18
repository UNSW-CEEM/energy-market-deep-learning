from marketsim.logbook.logbook import logbook
import pendulum

logbook().set_label("TEST"+" "+pendulum.now().format('ddd D/M HH:mm'))
logbook().record_hyperparameter('alpha', 1)
logbook().record_hyperparameter('beta', 2)
logbook().submit()