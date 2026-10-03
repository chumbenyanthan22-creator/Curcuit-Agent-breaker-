from setuptools import find_packages, setup

setup(
    name="agentbreaker",
    version="0.1.0",
    description="Loop detection and cost tracking for LangChain agents",
    packages=find_packages(),
    include_package_data=True,
    package_data={"agentbreaker": ["pricing_config.json"]},
    python_requires=">=3.11",
    install_requires=[
        "langchain-core>=1.0",
        "supabase>=2.0",
        "requests",
        "python-dotenv>=1.0.1",
    ],
)
