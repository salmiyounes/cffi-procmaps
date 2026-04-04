import nox

@nox.session
def tests(session):
    session.install(
        "pytest", "cffi"
    )
    session.install("-e", ".")
    session.run("pytest")    